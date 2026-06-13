const { AwsProvider } = require('./aws');
const store = require('./store');

const providers = new Map();

function ack(callback, fn) {
  if (typeof callback !== 'function') {
    return Promise.resolve(fn()).catch(() => {});
  }
  return Promise.resolve()
    .then(fn)
    .then((data) => callback({ ok: true, data }))
    .catch((err) => callback({ ok: false, error: err?.message || String(err), code: err?.name }));
}

function getAws(socket) {
  const entry = providers.get(socket.id);
  if (!entry || !entry.aws) throw new Error('Not authenticated to AWS. Call aws:authenticate first.');
  return entry.aws;
}

function registerAws(socket) {
  socket.on('aws:list-profiles', (_data, cb) => ack(cb, () => store.listProfiles('aws')));

  socket.on('aws:authenticate', async ({ accessKeyId, secretAccessKey, sessionToken, region, save, profileName, profileId }, cb) => {
    return ack(cb, async () => {
      let creds = { accessKeyId, secretAccessKey, sessionToken, region };
      let loadedProfileId = profileId || null;
      if (profileId && !accessKeyId) {
        const loaded = store.loadProfile('aws', profileId);
        if (!loaded) throw new Error(`AWS profile ${profileId} not found`);
        creds = { ...loaded.secrets, region: region || loaded.meta?.defaultRegion };
      }
      const provider = new AwsProvider(creds);
      await provider.authenticate();
      providers.set(socket.id, { ...(providers.get(socket.id) || {}), aws: provider, awsProfileId: loadedProfileId });

      if (save && !loadedProfileId) {
        const id = `aws-${Date.now()}`;
        store.saveProfile('aws', id, {
          accessKeyId: creds.accessKeyId,
          secretAccessKey: creds.secretAccessKey,
          sessionToken: creds.sessionToken || null,
        }, {
          name: profileName || `AWS ${creds.accessKeyId.slice(0, 4)}…${creds.accessKeyId.slice(-4)}`,
          defaultRegion: creds.region,
        });
        loadedProfileId = id;
        providers.get(socket.id).awsProfileId = id;
      }
      return { profileId: loadedProfileId, region: creds.region };
    });
  });

  socket.on('aws:logout', (_data, cb) => ack(cb, () => {
    const entry = providers.get(socket.id);
    if (entry) { delete entry.aws; delete entry.awsProfileId; }
    return { ok: true };
  }));

  socket.on('aws:delete-profile', ({ profileId }, cb) => ack(cb, () => store.deleteProfile('aws', profileId)));

  socket.on('aws:list-regions', (_data, cb) => ack(cb, () => getAws(socket).listRegions()));
  socket.on('aws:list-instance-types', ({ region }, cb) => ack(cb, () => getAws(socket).listInstanceTypes(region)));
  socket.on('aws:list-images', ({ region, ownerAlias, search }, cb) => ack(cb, () => getAws(socket).listImages(region, { ownerAlias, search })));
  socket.on('aws:list-keypairs', ({ region }, cb) => ack(cb, () => getAws(socket).listKeyPairs(region)));
  socket.on('aws:list-security-groups', ({ region }, cb) => ack(cb, () => getAws(socket).listSecurityGroups(region)));
  socket.on('aws:list-instances', ({ region }, cb) => ack(cb, () => getAws(socket).listInstances(region)));
  socket.on('aws:launch', (req, cb) => ack(cb, async () => {
    const provider = getAws(socket);
    const ids = await provider.launch(req);
    return { instanceIds: ids };
  }));
  socket.on('aws:start', ({ region, instanceIds }, cb) => ack(cb, () => getAws(socket).start(region, instanceIds)));
  socket.on('aws:stop', ({ region, instanceIds }, cb) => ack(cb, () => getAws(socket).stop(region, instanceIds)));
  socket.on('aws:terminate', ({ region, instanceIds }, cb) => ack(cb, () => getAws(socket).terminate(region, instanceIds)));

  socket.on('aws:get-key-material', ({ keyName }, cb) => ack(cb, () => {
    const { profileId } = providers.get(socket.id) || {};
    if (!profileId) return null;
    return store.loadKeyMaterial('aws', profileId, keyName);
  }));
}

function register(io) {
  io.on('connection', (socket) => {
    registerAws(socket);
    socket.on('disconnect', () => providers.delete(socket.id));
  });
}

module.exports = { register };
