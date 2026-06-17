import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { createAwsAdapter } from '../lib/cloud/awsAdapter';
import { useSocket } from '../context/SocketContext';
import type { CloudAdapter } from '../lib/cloud/adapter';
import { loadPrefs, patchProviderPrefs } from '../lib/cloud/store';
import type {
  AwsCredentials,
  CloudInstance,
  CloudLaunchRequest,
  CloudProfile,
  ProviderId,
} from '../lib/cloud/types';

interface UseCloudProvider {
  provider: ProviderId;
  adapter: CloudAdapter<AwsCredentials> | null;
  authenticated: boolean;
  authenticating: boolean;
  profiles: CloudProfile[];
  activeProfileId: string | null;
  region: string;
  setRegion: (r: string) => void;
  instances: CloudInstance[];
  loadingInstances: boolean;
  error: string | null;
  clearError: () => void;

  refreshProfiles: () => Promise<void>;
  authenticate: (creds: AwsCredentials) => Promise<void>;
  logout: () => Promise<void>;
  refreshInstances: () => Promise<void>;
  launch: (req: CloudLaunchRequest) => Promise<string[]>;
  start: (ids: string[]) => Promise<void>;
  stop: (ids: string[]) => Promise<void>;
  terminate: (ids: string[]) => Promise<void>;
  startPolling: () => void;
  stopPolling: () => void;
}

const POLL_INTERVAL_MS = 6000;

export default function useCloudProvider(provider: ProviderId): UseCloudProvider {
  const socket = useSocket();
  const adapter = useMemo<CloudAdapter<AwsCredentials> | null>(
    () => (provider === 'aws' ? createAwsAdapter(socket) : null),
    [provider, socket]
  );
  const prefs = loadPrefs()[provider] || {};

  const [authenticated, setAuthenticated] = useState(false);
  const [authenticating, setAuthenticating] = useState(false);
  const [profiles, setProfiles] = useState<CloudProfile[]>([]);
  const [activeProfileId, setActiveProfileId] = useState<string | null>(prefs.lastProfileId || null);
  const [region, setRegionState] = useState<string>(prefs.defaultRegion || 'us-east-1');
  const [instances, setInstances] = useState<CloudInstance[]>([]);
  const [loadingInstances, setLoadingInstances] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const setRegion = useCallback(
    (r: string) => {
      setRegionState(r);
      patchProviderPrefs(provider, { defaultRegion: r });
    },
    [provider]
  );

  const refreshProfiles = useCallback(async () => {
    if (!adapter) return;
    try {
      const list = await adapter.listProfiles();
      setProfiles(list);
    } catch (e: any) {
      setError(e?.message || String(e));
    }
  }, [adapter]);

  const authenticate = useCallback(
    async (creds: AwsCredentials) => {
      if (!adapter) return;
      setAuthenticating(true);
      setError(null);
      try {
        const res = await adapter.authenticate(creds);
        setAuthenticated(true);
        setActiveProfileId(res.profileId);
        setRegionState(res.region || region);
        patchProviderPrefs(provider, {
          lastProfileId: res.profileId,
          defaultRegion: res.region || region,
        });
        await refreshProfiles();
      } catch (e: any) {
        setAuthenticated(false);
        setError(e?.message || String(e));
        throw e;
      } finally {
        setAuthenticating(false);
      }
    },
    [adapter, provider, refreshProfiles, region]
  );

  const logout = useCallback(async () => {
    if (!adapter) return;
    await adapter.logout();
    setAuthenticated(false);
    setActiveProfileId(null);
    setInstances([]);
  }, [adapter]);

  const refreshInstances = useCallback(async () => {
    if (!adapter || !authenticated) return;
    setLoadingInstances(true);
    try {
      const list = await adapter.listInstances(region);
      setInstances(list);
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setLoadingInstances(false);
    }
  }, [adapter, authenticated, region]);

  const launch = useCallback(
    async (req: CloudLaunchRequest) => {
      if (!adapter) throw new Error('No cloud adapter');
      const res = await adapter.launch(req);
      patchProviderPrefs(provider, {
        lastInstanceType: req.instanceType,
        lastKeyName: req.keyName || null,
        lastSecurityGroupIds: req.securityGroupIds || [],
        lastImageId: req.imageId,
      });
      await refreshInstances();
      return res.instanceIds;
    },
    [adapter, provider, refreshInstances]
  );

  const start = useCallback(
    async (ids: string[]) => {
      if (!adapter) return;
      await adapter.start(region, ids);
      await refreshInstances();
    },
    [adapter, region, refreshInstances]
  );
  const stop = useCallback(
    async (ids: string[]) => {
      if (!adapter) return;
      await adapter.stop(region, ids);
      await refreshInstances();
    },
    [adapter, region, refreshInstances]
  );
  const terminate = useCallback(
    async (ids: string[]) => {
      if (!adapter) return;
      await adapter.terminate(region, ids);
      await refreshInstances();
    },
    [adapter, region, refreshInstances]
  );

  const stopPolling = useCallback(() => {
    if (pollTimer.current) {
      clearInterval(pollTimer.current);
      pollTimer.current = null;
    }
  }, []);

  const startPolling = useCallback(() => {
    stopPolling();
    pollTimer.current = setInterval(() => {
      refreshInstances();
    }, POLL_INTERVAL_MS);
  }, [refreshInstances, stopPolling]);

  useEffect(() => () => stopPolling(), [stopPolling]);

  useEffect(() => {
    if (adapter) refreshProfiles();
  }, [adapter, refreshProfiles]);

  return {
    provider,
    adapter,
    authenticated,
    authenticating,
    profiles,
    activeProfileId,
    region,
    setRegion,
    instances,
    loadingInstances,
    error,
    clearError,
    refreshProfiles,
    authenticate,
    logout,
    refreshInstances,
    launch,
    start,
    stop,
    terminate,
    startPolling,
    stopPolling,
  };
}
