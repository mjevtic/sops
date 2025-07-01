import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Switch } from '../components/ui/switch';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import { Alert, AlertDescription } from '../components/ui/alert';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Settings, 
  User, 
  Shield, 
  Bell, 
  Database, 
  Globe, 
  Lock, 
  Save,
  AlertTriangle,
  CheckCircle,
  Eye,
  EyeOff,
  Key,
  Mail,
  Clock,
  Activity,
  Zap
} from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../components/theme-provider';

export const SettingsPage = () => {
  const { user, changePassword } = useAuth();
  const { theme, setTheme } = useTheme();
  
  // Profile settings
  const [profileData, setProfileData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
    username: user?.username || '',
    bio: '',
    timezone: 'UTC',
    language: 'en'
  });

  // Password change
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false
  });

  // Security settings
  const [securitySettings, setSecuritySettings] = useState({
    two_factor_enabled: false,
    session_timeout: 30,
    login_notifications: true,
    failed_login_alerts: true,
    password_expiry_days: 90
  });

  // Notification settings
  const [notificationSettings, setNotificationSettings] = useState({
    email_notifications: true,
    rule_execution_alerts: true,
    integration_status_alerts: true,
    security_alerts: true,
    weekly_reports: true,
    digest_frequency: 'daily'
  });

  // System settings (admin only)
  const [systemSettings, setSystemSettings] = useState({
    maintenance_mode: false,
    debug_logging: false,
    rate_limit_enabled: true,
    max_requests_per_minute: 100,
    session_timeout_minutes: 30,
    password_min_length: 8,
    require_special_chars: true,
    audit_retention_days: 365
  });

  const [isLoading, setIsLoading] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null);

  const handleProfileSave = async () => {
    setIsLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSaveStatus({ type: 'success', message: 'Profile updated successfully' });
    } catch (error) {
      setSaveStatus({ type: 'error', message: 'Failed to update profile' });
    } finally {
      setIsLoading(false);
      setTimeout(() => setSaveStatus(null), 3000);
    }
  };

  const handlePasswordChange = async () => {
    if (passwordData.new_password !== passwordData.confirm_password) {
      setSaveStatus({ type: 'error', message: 'New passwords do not match' });
      return;
    }

    setIsLoading(true);
    try {
      const result = await changePassword(passwordData.current_password, passwordData.new_password);
      if (result.success) {
        setSaveStatus({ type: 'success', message: 'Password changed successfully' });
        setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
      } else {
        setSaveStatus({ type: 'error', message: result.error });
      }
    } catch (error) {
      setSaveStatus({ type: 'error', message: 'Failed to change password' });
    } finally {
      setIsLoading(false);
      setTimeout(() => setSaveStatus(null), 3000);
    }
  };

  const handleSecuritySave = async () => {
    setIsLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSaveStatus({ type: 'success', message: 'Security settings updated successfully' });
    } catch (error) {
      setSaveStatus({ type: 'error', message: 'Failed to update security settings' });
    } finally {
      setIsLoading(false);
      setTimeout(() => setSaveStatus(null), 3000);
    }
  };

  const handleNotificationSave = async () => {
    setIsLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSaveStatus({ type: 'success', message: 'Notification settings updated successfully' });
    } catch (error) {
      setSaveStatus({ type: 'error', message: 'Failed to update notification settings' });
    } finally {
      setIsLoading(false);
      setTimeout(() => setSaveStatus(null), 3000);
    }
  };

  const handleSystemSave = async () => {
    setIsLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSaveStatus({ type: 'success', message: 'System settings updated successfully' });
    } catch (error) {
      setSaveStatus({ type: 'error', message: 'Failed to update system settings' });
    } finally {
      setIsLoading(false);
      setTimeout(() => setSaveStatus(null), 3000);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Settings
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage your account, security, and system preferences
          </p>
        </div>
      </div>

      {/* Status Alert */}
      {saveStatus && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
        >
          <Alert variant={saveStatus.type === 'error' ? 'destructive' : 'default'}>
            {saveStatus.type === 'success' ? (
              <CheckCircle className="h-4 w-4" />
            ) : (
              <AlertTriangle className="h-4 w-4" />
            )}
            <AlertDescription>{saveStatus.message}</AlertDescription>
          </Alert>
        </motion.div>
      )}

      {/* Settings Tabs */}
      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2 lg:grid-cols-5">
          <TabsTrigger value="profile" className="flex items-center space-x-2">
            <User className="h-4 w-4" />
            <span className="hidden sm:inline">Profile</span>
          </TabsTrigger>
          <TabsTrigger value="security" className="flex items-center space-x-2">
            <Shield className="h-4 w-4" />
            <span className="hidden sm:inline">Security</span>
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center space-x-2">
            <Bell className="h-4 w-4" />
            <span className="hidden sm:inline">Notifications</span>
          </TabsTrigger>
          <TabsTrigger value="appearance" className="flex items-center space-x-2">
            <Globe className="h-4 w-4" />
            <span className="hidden sm:inline">Appearance</span>
          </TabsTrigger>
          {user?.role === 'admin' && (
            <TabsTrigger value="system" className="flex items-center space-x-2">
              <Settings className="h-4 w-4" />
              <span className="hidden sm:inline">System</span>
            </TabsTrigger>
          )}
        </TabsList>

        {/* Profile Settings */}
        <TabsContent value="profile">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <User className="h-5 w-5" />
                <span>Profile Information</span>
              </CardTitle>
              <CardDescription>
                Update your personal information and account details
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="full_name">Full Name</Label>
                  <Input
                    id="full_name"
                    value={profileData.full_name}
                    onChange={(e) => setProfileData({...profileData, full_name: e.target.value})}
                    placeholder="Enter your full name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="username">Username</Label>
                  <Input
                    id="username"
                    value={profileData.username}
                    onChange={(e) => setProfileData({...profileData, username: e.target.value})}
                    placeholder="Enter your username"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    value={profileData.email}
                    onChange={(e) => setProfileData({...profileData, email: e.target.value})}
                    placeholder="Enter your email"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="timezone">Timezone</Label>
                  <Select value={profileData.timezone} onValueChange={(value) => setProfileData({...profileData, timezone: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="UTC">UTC</SelectItem>
                      <SelectItem value="America/New_York">Eastern Time</SelectItem>
                      <SelectItem value="America/Chicago">Central Time</SelectItem>
                      <SelectItem value="America/Denver">Mountain Time</SelectItem>
                      <SelectItem value="America/Los_Angeles">Pacific Time</SelectItem>
                      <SelectItem value="Europe/London">London</SelectItem>
                      <SelectItem value="Europe/Paris">Paris</SelectItem>
                      <SelectItem value="Asia/Tokyo">Tokyo</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="bio">Bio</Label>
                <Textarea
                  id="bio"
                  value={profileData.bio}
                  onChange={(e) => setProfileData({...profileData, bio: e.target.value})}
                  placeholder="Tell us about yourself..."
                  rows={3}
                />
              </div>

              <Separator />

              {/* Password Change Section */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white flex items-center space-x-2">
                  <Key className="h-5 w-5" />
                  <span>Change Password</span>
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="current_password">Current Password</Label>
                    <div className="relative">
                      <Input
                        id="current_password"
                        type={showPasswords.current ? 'text' : 'password'}
                        value={passwordData.current_password}
                        onChange={(e) => setPasswordData({...passwordData, current_password: e.target.value})}
                        placeholder="Enter current password"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3"
                        onClick={() => setShowPasswords({...showPasswords, current: !showPasswords.current})}
                      >
                        {showPasswords.current ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="new_password">New Password</Label>
                    <div className="relative">
                      <Input
                        id="new_password"
                        type={showPasswords.new ? 'text' : 'password'}
                        value={passwordData.new_password}
                        onChange={(e) => setPasswordData({...passwordData, new_password: e.target.value})}
                        placeholder="Enter new password"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3"
                        onClick={() => setShowPasswords({...showPasswords, new: !showPasswords.new})}
                      >
                        {showPasswords.new ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="confirm_password">Confirm Password</Label>
                    <div className="relative">
                      <Input
                        id="confirm_password"
                        type={showPasswords.confirm ? 'text' : 'password'}
                        value={passwordData.confirm_password}
                        onChange={(e) => setPasswordData({...passwordData, confirm_password: e.target.value})}
                        placeholder="Confirm new password"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3"
                        onClick={() => setShowPasswords({...showPasswords, confirm: !showPasswords.confirm})}
                      >
                        {showPasswords.confirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                </div>
                
                <Button onClick={handlePasswordChange} disabled={isLoading} variant="outline">
                  <Lock className="h-4 w-4 mr-2" />
                  Change Password
                </Button>
              </div>

              <div className="flex justify-end">
                <Button onClick={handleProfileSave} disabled={isLoading}>
                  <Save className="h-4 w-4 mr-2" />
                  {isLoading ? 'Saving...' : 'Save Profile'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Settings */}
        <TabsContent value="security">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Shield className="h-5 w-5" />
                <span>Security Settings</span>
              </CardTitle>
              <CardDescription>
                Configure security features and access controls
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Two-Factor Authentication</Label>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Add an extra layer of security to your account
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={securitySettings.two_factor_enabled}
                      onCheckedChange={(checked) => setSecuritySettings({...securitySettings, two_factor_enabled: checked})}
                    />
                    <Badge variant={securitySettings.two_factor_enabled ? 'default' : 'secondary'}>
                      {securitySettings.two_factor_enabled ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </div>
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Login Notifications</Label>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Get notified when someone logs into your account
                    </p>
                  </div>
                  <Switch
                    checked={securitySettings.login_notifications}
                    onCheckedChange={(checked) => setSecuritySettings({...securitySettings, login_notifications: checked})}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Failed Login Alerts</Label>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Alert when failed login attempts are detected
                    </p>
                  </div>
                  <Switch
                    checked={securitySettings.failed_login_alerts}
                    onCheckedChange={(checked) => setSecuritySettings({...securitySettings, failed_login_alerts: checked})}
                  />
                </div>

                <Separator />

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="session_timeout">Session Timeout (minutes)</Label>
                    <Input
                      id="session_timeout"
                      type="number"
                      value={securitySettings.session_timeout}
                      onChange={(e) => setSecuritySettings({...securitySettings, session_timeout: parseInt(e.target.value)})}
                      min="5"
                      max="480"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="password_expiry">Password Expiry (days)</Label>
                    <Input
                      id="password_expiry"
                      type="number"
                      value={securitySettings.password_expiry_days}
                      onChange={(e) => setSecuritySettings({...securitySettings, password_expiry_days: parseInt(e.target.value)})}
                      min="30"
                      max="365"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end">
                <Button onClick={handleSecuritySave} disabled={isLoading}>
                  <Save className="h-4 w-4 mr-2" />
                  {isLoading ? 'Saving...' : 'Save Security Settings'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notification Settings */}
        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Bell className="h-5 w-5" />
                <span>Notification Preferences</span>
              </CardTitle>
              <CardDescription>
                Choose what notifications you want to receive
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Email Notifications</Label>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Receive notifications via email
                    </p>
                  </div>
                  <Switch
                    checked={notificationSettings.email_notifications}
                    onCheckedChange={(checked) => setNotificationSettings({...notificationSettings, email_notifications: checked})}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Rule Execution Alerts</Label>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Get notified when automation rules are executed
                    </p>
                  </div>
                  <Switch
                    checked={notificationSettings.rule_execution_alerts}
                    onCheckedChange={(checked) => setNotificationSettings({...notificationSettings, rule_execution_alerts: checked})}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Integration Status Alerts</Label>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Alert when integrations go offline or have issues
                    </p>
                  </div>
                  <Switch
                    checked={notificationSettings.integration_status_alerts}
                    onCheckedChange={(checked) => setNotificationSettings({...notificationSettings, integration_status_alerts: checked})}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Security Alerts</Label>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Important security notifications and warnings
                    </p>
                  </div>
                  <Switch
                    checked={notificationSettings.security_alerts}
                    onCheckedChange={(checked) => setNotificationSettings({...notificationSettings, security_alerts: checked})}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Weekly Reports</Label>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Receive weekly summary reports
                    </p>
                  </div>
                  <Switch
                    checked={notificationSettings.weekly_reports}
                    onCheckedChange={(checked) => setNotificationSettings({...notificationSettings, weekly_reports: checked})}
                  />
                </div>

                <Separator />

                <div className="space-y-2">
                  <Label htmlFor="digest_frequency">Digest Frequency</Label>
                  <Select 
                    value={notificationSettings.digest_frequency} 
                    onValueChange={(value) => setNotificationSettings({...notificationSettings, digest_frequency: value})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="immediate">Immediate</SelectItem>
                      <SelectItem value="hourly">Hourly</SelectItem>
                      <SelectItem value="daily">Daily</SelectItem>
                      <SelectItem value="weekly">Weekly</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex justify-end">
                <Button onClick={handleNotificationSave} disabled={isLoading}>
                  <Save className="h-4 w-4 mr-2" />
                  {isLoading ? 'Saving...' : 'Save Notification Settings'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Appearance Settings */}
        <TabsContent value="appearance">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Globe className="h-5 w-5" />
                <span>Appearance & Language</span>
              </CardTitle>
              <CardDescription>
                Customize the look and feel of your interface
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Theme</Label>
                  <Select value={theme} onValueChange={setTheme}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="light">Light</SelectItem>
                      <SelectItem value="dark">Dark</SelectItem>
                      <SelectItem value="system">System</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Choose your preferred color scheme
                  </p>
                </div>

                <div className="space-y-2">
                  <Label>Language</Label>
                  <Select value={profileData.language} onValueChange={(value) => setProfileData({...profileData, language: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="es">Español</SelectItem>
                      <SelectItem value="fr">Français</SelectItem>
                      <SelectItem value="de">Deutsch</SelectItem>
                      <SelectItem value="ja">日本語</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* System Settings (Admin Only) */}
        {user?.role === 'admin' && (
          <TabsContent value="system">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Settings className="h-5 w-5" />
                  <span>System Configuration</span>
                  <Badge variant="destructive">Admin Only</Badge>
                </CardTitle>
                <CardDescription>
                  Configure system-wide settings and security policies
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Maintenance Mode</Label>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Temporarily disable system access for maintenance
                      </p>
                    </div>
                    <Switch
                      checked={systemSettings.maintenance_mode}
                      onCheckedChange={(checked) => setSystemSettings({...systemSettings, maintenance_mode: checked})}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Debug Logging</Label>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Enable detailed logging for troubleshooting
                      </p>
                    </div>
                    <Switch
                      checked={systemSettings.debug_logging}
                      onCheckedChange={(checked) => setSystemSettings({...systemSettings, debug_logging: checked})}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Rate Limiting</Label>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Protect against abuse with request rate limiting
                      </p>
                    </div>
                    <Switch
                      checked={systemSettings.rate_limit_enabled}
                      onCheckedChange={(checked) => setSystemSettings({...systemSettings, rate_limit_enabled: checked})}
                    />
                  </div>

                  <Separator />

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="max_requests">Max Requests per Minute</Label>
                      <Input
                        id="max_requests"
                        type="number"
                        value={systemSettings.max_requests_per_minute}
                        onChange={(e) => setSystemSettings({...systemSettings, max_requests_per_minute: parseInt(e.target.value)})}
                        min="10"
                        max="1000"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="session_timeout_sys">Session Timeout (minutes)</Label>
                      <Input
                        id="session_timeout_sys"
                        type="number"
                        value={systemSettings.session_timeout_minutes}
                        onChange={(e) => setSystemSettings({...systemSettings, session_timeout_minutes: parseInt(e.target.value)})}
                        min="5"
                        max="480"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="password_min_length">Minimum Password Length</Label>
                      <Input
                        id="password_min_length"
                        type="number"
                        value={systemSettings.password_min_length}
                        onChange={(e) => setSystemSettings({...systemSettings, password_min_length: parseInt(e.target.value)})}
                        min="6"
                        max="32"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="audit_retention">Audit Log Retention (days)</Label>
                      <Input
                        id="audit_retention"
                        type="number"
                        value={systemSettings.audit_retention_days}
                        onChange={(e) => setSystemSettings({...systemSettings, audit_retention_days: parseInt(e.target.value)})}
                        min="30"
                        max="2555"
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Require Special Characters in Passwords</Label>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Enforce special character requirements for passwords
                      </p>
                    </div>
                    <Switch
                      checked={systemSettings.require_special_chars}
                      onCheckedChange={(checked) => setSystemSettings({...systemSettings, require_special_chars: checked})}
                    />
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button onClick={handleSystemSave} disabled={isLoading} variant="destructive">
                    <Save className="h-4 w-4 mr-2" />
                    {isLoading ? 'Saving...' : 'Save System Settings'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
};

