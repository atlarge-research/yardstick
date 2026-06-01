const {
  EC2Client,
  DescribeRegionsCommand,
  DescribeInstanceTypeOfferingsCommand,
  DescribeImagesCommand,
  DescribeKeyPairsCommand,
  DescribeSecurityGroupsCommand,
  DescribeInstancesCommand,
  RunInstancesCommand,
  StartInstancesCommand,
  StopInstancesCommand,
  TerminateInstancesCommand,
  ImportKeyPairCommand,
  CreateKeyPairCommand,
} = require('@aws-sdk/client-ec2');

const DEFAULT_USERNAME_BY_AMI_NAME_PREFIX = [
  { prefix: 'amzn', user: 'ec2-user' },
  { prefix: 'amazon', user: 'ec2-user' },
  { prefix: 'al2023', user: 'ec2-user' },
  { prefix: 'ubuntu', user: 'ubuntu' },
  { prefix: 'debian', user: 'admin' },
  { prefix: 'rhel', user: 'ec2-user' },
  { prefix: 'centos', user: 'centos' },
  { prefix: 'suse', user: 'ec2-user' },
];

function defaultUserForImage(imageName) {
  if (!imageName) return 'ec2-user';
  const lower = imageName.toLowerCase();
  for (const { prefix, user } of DEFAULT_USERNAME_BY_AMI_NAME_PREFIX) {
    if (lower.startsWith(prefix)) return user;
  }
  return 'ec2-user';
}

function stateName(s) {
  const map = {
    0: 'pending',
    16: 'running',
    32: 'shutting-down',
    48: 'terminated',
    64: 'stopping',
    80: 'stopped',
  };
  if (s == null) return 'unknown';
  if (typeof s === 'object') return s.Name || map[s.Code] || 'unknown';
  return map[s] || 'unknown';
}

class AwsProvider {
  constructor({ accessKeyId, secretAccessKey, sessionToken, region }) {
    if (!accessKeyId || !secretAccessKey) throw new Error('AWS access key and secret are required');
    this.defaultRegion = region || 'us-east-1';
    this.credentials = { accessKeyId, secretAccessKey };
    if (sessionToken) this.credentials.sessionToken = sessionToken;
    this._clients = new Map();
  }

  _client(region) {
    const r = region || this.defaultRegion;
    if (!this._clients.has(r)) {
      this._clients.set(r, new EC2Client({ region: r, credentials: this.credentials }));
    }
    return this._clients.get(r);
  }

  async authenticate() {
    const client = this._client(this.defaultRegion);
    const res = await client.send(new DescribeRegionsCommand({ AllRegions: false }));
    return { ok: true, regionCount: (res.Regions || []).length };
  }

  async listRegions() {
    const client = this._client(this.defaultRegion);
    const res = await client.send(new DescribeRegionsCommand({ AllRegions: false }));
    return (res.Regions || [])
      .map((r) => ({ id: r.RegionName, name: r.RegionName }))
      .sort((a, b) => a.id.localeCompare(b.id));
  }

  async listInstanceTypes(region) {
    const client = this._client(region);
    const popular = ['t3.micro', 't3.small', 't3.medium', 't3.large', 't3.xlarge', 't3.2xlarge',
      't3a.medium', 't3a.large', 'm5.large', 'm5.xlarge', 'm5.2xlarge', 'm5.4xlarge',
      'c5.large', 'c5.xlarge', 'c5.2xlarge', 'c5.4xlarge', 'r5.large', 'r5.xlarge'];
    const seen = new Set();
    const types = [];
    let nextToken;
    do {
      const res = await client.send(new DescribeInstanceTypeOfferingsCommand({
        LocationType: 'region',
        Filters: [{ Name: 'location', Values: [region] }],
        MaxResults: 100,
        NextToken: nextToken,
      }));
      (res.InstanceTypeOfferings || []).forEach((o) => {
        if (!seen.has(o.InstanceType)) {
          seen.add(o.InstanceType);
          types.push(o.InstanceType);
        }
      });
      nextToken = res.NextToken;
      if (types.length > 600) break;
    } while (nextToken);
    const preferred = popular.filter((t) => seen.has(t));
    const rest = types.filter((t) => !preferred.includes(t)).sort();
    return [...preferred, ...rest];
  }

  async listImages(region, { ownerAlias = 'amazon', search = 'al2023-ami' } = {}) {
    const client = this._client(region);
    const res = await client.send(new DescribeImagesCommand({
      Owners: [ownerAlias],
      Filters: [
        { Name: 'name', Values: [`*${search}*`] },
        { Name: 'state', Values: ['available'] },
        { Name: 'architecture', Values: ['x86_64'] },
      ],
      MaxResults: 50,
    }));
    return (res.Images || [])
      .map((i) => ({
        id: i.ImageId,
        name: i.Name,
        description: i.Description,
        createdAt: i.CreationDate,
        defaultUser: defaultUserForImage(i.Name),
      }))
      .sort((a, b) => (b.createdAt || '').localeCompare(a.createdAt || ''))
      .slice(0, 25);
  }

  async listKeyPairs(region) {
    const client = this._client(region);
    const res = await client.send(new DescribeKeyPairsCommand({}));
    return (res.KeyPairs || []).map((k) => k.KeyName).filter(Boolean);
  }

  async listSecurityGroups(region) {
    const client = this._client(region);
    const res = await client.send(new DescribeSecurityGroupsCommand({}));
    return (res.SecurityGroups || []).map((g) => ({
      id: g.GroupId,
      name: g.GroupName,
      description: g.Description,
      vpcId: g.VpcId,
    }));
  }

  async _imageNameMap(region, imageIds) {
    const unique = [...new Set(imageIds.filter(Boolean))];
    if (unique.length === 0) return {};
    try {
      const client = this._client(region);
      const res = await client.send(new DescribeImagesCommand({ ImageIds: unique }));
      const map = {};
      (res.Images || []).forEach((img) => { map[img.ImageId] = img.Name || ''; });
      return map;
    } catch {
      return {};
    }
  }

  async listInstances(region) {
    const client = this._client(region);
    const res = await client.send(new DescribeInstancesCommand({
      Filters: [{ Name: 'instance-state-name', Values: ['pending', 'running', 'stopping', 'stopped'] }],
    }));
    const raw = [];
    (res.Reservations || []).forEach((r) => {
      (r.Instances || []).forEach((i) => raw.push(i));
    });
    const imageNames = await this._imageNameMap(region, raw.map((i) => i.ImageId));
    const items = raw.map((i) => {
      const nameTag = (i.Tags || []).find((t) => t.Key === 'Name');
      return {
        id: i.InstanceId,
        provider: 'aws',
        region,
        name: nameTag?.Value || null,
        state: stateName(i.State),
        publicIp: i.PublicIpAddress || null,
        privateIp: i.PrivateIpAddress || null,
        instanceType: i.InstanceType,
        keyName: i.KeyName || null,
        imageId: i.ImageId,
        launchedAt: i.LaunchTime ? new Date(i.LaunchTime).toISOString() : null,
        defaultUsername: defaultUserForImage(imageNames[i.ImageId] || ''),
      };
    });
    return items.sort((a, b) => (b.launchedAt || '').localeCompare(a.launchedAt || ''));
  }

  async describeInstances(region, ids) {
    if (!ids || ids.length === 0) return [];
    const client = this._client(region);
    const res = await client.send(new DescribeInstancesCommand({ InstanceIds: ids }));
    const raw = [];
    (res.Reservations || []).forEach((r) => {
      (r.Instances || []).forEach((i) => raw.push(i));
    });
    const imageNames = await this._imageNameMap(region, raw.map((i) => i.ImageId));
    return raw.map((i) => {
      const nameTag = (i.Tags || []).find((t) => t.Key === 'Name');
      return {
        id: i.InstanceId,
        provider: 'aws',
        region,
        name: nameTag?.Value || null,
        state: stateName(i.State),
        publicIp: i.PublicIpAddress || null,
        privateIp: i.PrivateIpAddress || null,
        instanceType: i.InstanceType,
        keyName: i.KeyName || null,
        imageId: i.ImageId,
        launchedAt: i.LaunchTime ? new Date(i.LaunchTime).toISOString() : null,
        defaultUsername: defaultUserForImage(imageNames[i.ImageId] || ''),
      };
    });
  }

  async launch({ region, imageId, instanceType, keyName, securityGroupIds = [], count = 1, name }) {
    const client = this._client(region);
    const tagSpec = name
      ? [{ ResourceType: 'instance', Tags: [{ Key: 'Name', Value: name }, { Key: 'yardstick', Value: 'true' }] }]
      : [{ ResourceType: 'instance', Tags: [{ Key: 'yardstick', Value: 'true' }] }];
    const res = await client.send(new RunInstancesCommand({
      ImageId: imageId,
      InstanceType: instanceType,
      MinCount: count,
      MaxCount: count,
      KeyName: keyName || undefined,
      SecurityGroupIds: securityGroupIds.length ? securityGroupIds : undefined,
      TagSpecifications: tagSpec,
    }));
    const ids = (res.Instances || []).map((i) => i.InstanceId);
    return ids;
  }

  async start(region, ids) {
    const client = this._client(region);
    await client.send(new StartInstancesCommand({ InstanceIds: ids }));
  }

  async stop(region, ids) {
    const client = this._client(region);
    await client.send(new StopInstancesCommand({ InstanceIds: ids }));
  }

  async terminate(region, ids) {
    const client = this._client(region);
    await client.send(new TerminateInstancesCommand({ InstanceIds: ids }));
  }

  async importKeyPair(region, keyName, publicKeyMaterial) {
    const client = this._client(region);
    await client.send(new ImportKeyPairCommand({
      KeyName: keyName,
      PublicKeyMaterial: Buffer.from(publicKeyMaterial),
    }));
  }

  async createKeyPair(region, keyName) {
    const client = this._client(region);
    const res = await client.send(new CreateKeyPairCommand({ KeyName: keyName, KeyType: 'rsa', KeyFormat: 'pem' }));
    return { keyName: res.KeyName, fingerprint: res.KeyFingerprint, privateKey: res.KeyMaterial };
  }
}

module.exports = { AwsProvider, defaultUserForImage };
