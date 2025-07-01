import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Alert, AlertDescription } from '../components/ui/alert';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuLabel, 
  DropdownMenuSeparator, 
  DropdownMenuTrigger 
} from '../components/ui/dropdown-menu';
import { 
  Puzzle, 
  Plus, 
  Settings, 
  Trash2, 
  TestTube, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle,
  ExternalLink,
  MoreHorizontal,
  Zap,
  Shield,
  Activity
} from 'lucide-react';
import { motion } from 'framer-motion';

// Platform configurations
const platforms = {
  slack: {
    name: 'Slack',
    description: 'Send messages, create channels, and manage Slack workspaces',
    icon: '💬',
    color: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
    setupUrl: 'https://api.slack.com/apps',
    requiredFields: [
      { name: 'bot_token', label: 'Bot Token', type: 'password', placeholder: 'xoxb-...' },
      { name: 'signing_secret', label: 'Signing Secret (Optional)', type: 'password', placeholder: 'abc123...' }
    ],
    actions: ['Send Message', 'Send DM', 'Create Channel', 'Invite Users']
  },
  trello: {
    name: 'Trello',
    description: 'Create cards, manage boards, and automate Trello workflows',
    icon: '📋',
    color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    setupUrl: 'https://trello.com/app-key',
    requiredFields: [
      { name: 'api_key', label: 'API Key', type: 'text', placeholder: 'Your API key' },
      { name: 'api_token', label: 'API Token', type: 'password', placeholder: 'Your API token' }
    ],
    actions: ['Create Card', 'Move Card', 'Add Comment', 'Create Checklist']
  },
  notion: {
    name: 'Notion',
    description: 'Create pages, manage databases, and organize Notion workspaces',
    icon: '📝',
    color: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
    setupUrl: 'https://www.notion.so/my-integrations',
    requiredFields: [
      { name: 'api_token', label: 'Integration Token', type: 'password', placeholder: 'secret_...' }
    ],
    actions: ['Create Page', 'Update Page', 'Add Comment', 'Query Database']
  },
  google_sheets: {
    name: 'Google Sheets',
    description: 'Manage spreadsheets, append data, and automate Google Sheets workflows',
    icon: '📊',
    color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    setupUrl: 'https://console.developers.google.com/',
    requiredFields: [
      { name: 'access_token', label: 'Access Token', type: 'password', placeholder: 'ya29...' },
      { name: 'refresh_token', label: 'Refresh Token (Optional)', type: 'password', placeholder: '1//...' }
    ],
    actions: ['Append Row', 'Update Row', 'Create Sheet', 'Batch Update']
  }
};

// Mock data - replace with real API calls
const mockIntegrations = [
  {
    id: 1,
    platform: 'slack',
    name: 'Main Workspace',
    status: 'active',
    lastHealthCheck: '2 minutes ago',
    healthStatus: 'healthy',
    totalActions: 156,
    lastActionAt: '5 minutes ago',
    created: '2024-01-15',
    config: {
      default_channel: '#support',
      bot_name: 'SupportOps Bot'
    }
  },
  {
    id: 2,
    platform: 'trello',
    name: 'Support Board',
    status: 'active',
    lastHealthCheck: '1 hour ago',
    healthStatus: 'healthy',
    totalActions: 89,
    lastActionAt: '30 minutes ago',
    created: '2024-01-10',
    config: {
      default_board_id: 'abc123',
      default_list_id: 'def456'
    }
  },
  {
    id: 3,
    platform: 'notion',
    name: 'Knowledge Base',
    status: 'error',
    lastHealthCheck: '3 hours ago',
    healthStatus: 'unhealthy',
    totalActions: 23,
    lastActionAt: '2 days ago',
    created: '2024-01-05',
    lastError: 'Invalid API token',
    config: {
      database_id: 'xyz789'
    }
  }
];

const getStatusColor = (status) => {
  switch (status) {
    case 'active':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    case 'inactive':
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    case 'error':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    default:
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
  }
};

const getStatusIcon = (status) => {
  switch (status) {
    case 'active':
      return <CheckCircle className="h-4 w-4" />;
    case 'inactive':
      return <Clock className="h-4 w-4" />;
    case 'error':
      return <XCircle className="h-4 w-4" />;
    default:
      return <AlertTriangle className="h-4 w-4" />;
  }
};

const PlatformCard = ({ platformKey, platform, onConnect }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3 }}
  >
    <Card className="hover:shadow-lg transition-shadow duration-200 cursor-pointer group">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="text-2xl">{platform.icon}</div>
            <div>
              <CardTitle className="text-lg">{platform.name}</CardTitle>
              <CardDescription className="text-sm">
                {platform.description}
              </CardDescription>
            </div>
          </div>
          <Button 
            onClick={() => onConnect(platformKey)}
            size="sm"
            className="opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <Plus className="h-4 w-4 mr-2" />
            Connect
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex flex-wrap gap-1">
            {platform.actions.slice(0, 3).map((action, index) => (
              <Badge key={index} variant="secondary" className="text-xs">
                {action}
              </Badge>
            ))}
            {platform.actions.length > 3 && (
              <Badge variant="secondary" className="text-xs">
                +{platform.actions.length - 3} more
              </Badge>
            )}
          </div>
          <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
            <span>Setup required</span>
            <a 
              href={platform.setupUrl} 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex items-center space-x-1 hover:text-blue-600 dark:hover:text-blue-400"
            >
              <span>Documentation</span>
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>
      </CardContent>
    </Card>
  </motion.div>
);

const IntegrationCard = ({ integration, onEdit, onDelete, onTest }) => {
  const platform = platforms[integration.platform];
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="hover:shadow-lg transition-shadow duration-200">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="text-2xl">{platform.icon}</div>
              <div>
                <CardTitle className="text-lg flex items-center space-x-2">
                  <span>{integration.name}</span>
                  <Badge variant="outline" className={getStatusColor(integration.status)}>
                    {getStatusIcon(integration.status)}
                    <span className="ml-1">{integration.status}</span>
                  </Badge>
                </CardTitle>
                <CardDescription>
                  {platform.name} • {integration.totalActions} actions executed
                </CardDescription>
              </div>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>Actions</DropdownMenuLabel>
                <DropdownMenuItem onClick={() => onTest(integration)}>
                  <TestTube className="mr-2 h-4 w-4" />
                  Test Connection
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onEdit(integration)}>
                  <Settings className="mr-2 h-4 w-4" />
                  Configure
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem 
                  onClick={() => onDelete(integration)}
                  className="text-red-600 dark:text-red-400"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Remove
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {integration.status === 'error' && integration.lastError && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  {integration.lastError}
                </AlertDescription>
              </Alert>
            )}
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500 dark:text-gray-400">Health Status</p>
                <p className={`font-medium ${integration.healthStatus === 'healthy' ? 'text-green-600' : 'text-red-600'}`}>
                  {integration.healthStatus}
                </p>
              </div>
              <div>
                <p className="text-gray-500 dark:text-gray-400">Last Check</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {integration.lastHealthCheck}
                </p>
              </div>
              <div>
                <p className="text-gray-500 dark:text-gray-400">Last Action</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {integration.lastActionAt}
                </p>
              </div>
              <div>
                <p className="text-gray-500 dark:text-gray-400">Created</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {integration.created}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

const ConnectIntegrationDialog = ({ isOpen, onClose, platformKey, onConnect }) => {
  const [formData, setFormData] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const platform = platforms[platformKey];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock success
      onConnect({
        platform: platformKey,
        name: `${platform.name} Integration`,
        credentials: formData,
        config: {}
      });
      
      onClose();
      setFormData({});
    } catch (err) {
      setError('Failed to connect integration. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (fieldName, value) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  if (!platform) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <span className="text-xl">{platform.icon}</span>
            <span>Connect {platform.name}</span>
          </DialogTitle>
          <DialogDescription>
            Enter your {platform.name} credentials to connect this integration.
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          <div className="space-y-4">
            <div>
              <Label htmlFor="integration-name">Integration Name</Label>
              <Input
                id="integration-name"
                placeholder={`My ${platform.name} Integration`}
                value={formData.name || ''}
                onChange={(e) => handleInputChange('name', e.target.value)}
                required
              />
            </div>
            
            {platform.requiredFields.map((field) => (
              <div key={field.name}>
                <Label htmlFor={field.name}>{field.label}</Label>
                <Input
                  id={field.name}
                  type={field.type}
                  placeholder={field.placeholder}
                  value={formData[field.name] || ''}
                  onChange={(e) => handleInputChange(field.name, e.target.value)}
                  required={!field.label.includes('Optional')}
                />
              </div>
            ))}
            
            <div>
              <Label htmlFor="description">Description (Optional)</Label>
              <Textarea
                id="description"
                placeholder="Describe how this integration will be used..."
                value={formData.description || ''}
                onChange={(e) => handleInputChange('description', e.target.value)}
                rows={3}
              />
            </div>
          </div>
          
          <div className="flex items-center justify-between pt-4">
            <a 
              href={platform.setupUrl} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200 flex items-center space-x-1"
            >
              <span>Setup Guide</span>
              <ExternalLink className="h-3 w-3" />
            </a>
            
            <div className="flex space-x-2">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Connecting...</span>
                  </div>
                ) : (
                  'Connect'
                )}
              </Button>
            </div>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export const IntegrationsPage = () => {
  const [integrations, setIntegrations] = useState(mockIntegrations);
  const [connectDialogOpen, setConnectDialogOpen] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState(null);

  const connectedPlatforms = integrations.map(i => i.platform);
  const availablePlatforms = Object.keys(platforms).filter(p => !connectedPlatforms.includes(p));

  const handleConnect = (platformKey) => {
    setSelectedPlatform(platformKey);
    setConnectDialogOpen(true);
  };

  const handleConnectSubmit = (integrationData) => {
    const newIntegration = {
      id: Math.max(...integrations.map(i => i.id)) + 1,
      platform: integrationData.platform,
      name: integrationData.name,
      status: 'active',
      lastHealthCheck: 'Just now',
      healthStatus: 'healthy',
      totalActions: 0,
      lastActionAt: 'Never',
      created: new Date().toISOString().split('T')[0],
      config: integrationData.config
    };
    
    setIntegrations([...integrations, newIntegration]);
  };

  const handleEdit = (integration) => {
    console.log('Edit integration:', integration);
    // TODO: Open edit dialog
  };

  const handleDelete = (integration) => {
    setIntegrations(integrations.filter(i => i.id !== integration.id));
  };

  const handleTest = async (integration) => {
    console.log('Test integration:', integration);
    // TODO: Test connection
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Integrations
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Connect and manage your third-party service integrations
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Puzzle className="h-5 w-5 text-blue-600" />
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {integrations.length}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Connected Integrations
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Activity className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {integrations.filter(i => i.status === 'active').length}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Active Integrations
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Shield className="h-5 w-5 text-purple-600" />
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {integrations.filter(i => i.healthStatus === 'healthy').length}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Healthy Connections
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Connected Integrations */}
      {integrations.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Connected Integrations
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {integrations.map((integration) => (
              <IntegrationCard
                key={integration.id}
                integration={integration}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onTest={handleTest}
              />
            ))}
          </div>
        </div>
      )}

      {/* Available Platforms */}
      {availablePlatforms.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Available Integrations
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {availablePlatforms.map((platformKey) => (
              <PlatformCard
                key={platformKey}
                platformKey={platformKey}
                platform={platforms[platformKey]}
                onConnect={handleConnect}
              />
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {integrations.length === 0 && (
        <Card>
          <CardContent className="p-12 text-center">
            <Puzzle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No integrations connected
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-6">
              Connect your first integration to start automating your workflows
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
              {Object.entries(platforms).slice(0, 4).map(([key, platform]) => (
                <Button
                  key={key}
                  variant="outline"
                  onClick={() => handleConnect(key)}
                  className="flex items-center space-x-2 h-auto p-4"
                >
                  <span className="text-lg">{platform.icon}</span>
                  <span>Connect {platform.name}</span>
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Connect Integration Dialog */}
      <ConnectIntegrationDialog
        isOpen={connectDialogOpen}
        onClose={() => {
          setConnectDialogOpen(false);
          setSelectedPlatform(null);
        }}
        platformKey={selectedPlatform}
        onConnect={handleConnectSubmit}
      />
    </div>
  );
};

