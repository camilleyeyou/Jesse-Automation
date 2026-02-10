import { useState, useEffect, useCallback } from 'react';
import {
  Play, Square, Clock, Send, Sparkles, Calendar,
  History, RefreshCw, AlertCircle, CheckCircle,
  Linkedin, Image, FileText, Zap, BarChart3, X, ZoomIn, Video,
  MessageCircle, ExternalLink, ThumbsUp, MessageSquare, Copy, Check,
  Menu, ChevronRight
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001';

// ============== API Functions ==============

const api = {
  async get(endpoint) {
    const res = await fetch(`${API_BASE}${endpoint}`);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  },
  async post(endpoint, data = {}) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  },
  async patch(endpoint, data = {}) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  },
  async delete(endpoint) {
    const res = await fetch(`${API_BASE}${endpoint}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  }
};

// Helper to get full image URL
const getImageUrl = (imagePath) => {
  if (!imagePath) return null;
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
    return imagePath;
  }
  if (imagePath.startsWith('/images')) {
    return `${API_BASE}${imagePath}`;
  }
  if (imagePath.includes('data/images/')) {
    const filename = imagePath.split('/').pop();
    return `${API_BASE}/images/${filename}`;
  }
  return `${API_BASE}/images/${imagePath}`;
};

// Helper to get full video URL
const getVideoUrl = (videoPath) => {
  if (!videoPath) return null;
  if (videoPath.startsWith('http://') || videoPath.startsWith('https://')) {
    return videoPath;
  }
  if (videoPath.startsWith('/videos')) {
    return `${API_BASE}${videoPath}`;
  }
  if (videoPath.includes('data/images/videos/')) {
    const filename = videoPath.split('/').pop();
    return `${API_BASE}/videos/${filename}`;
  }
  return `${API_BASE}/videos/${videoPath}`;
};

// ============== Components ==============

function StatusBadge({ active, label }) {
  return (
    <span className={`px-2.5 py-1 sm:px-3 rounded-full text-xs sm:text-sm font-medium inline-flex items-center gap-1.5 transition-all duration-200 ${
      active
        ? 'bg-green-500/20 text-green-400 border border-green-500/30 shadow-green-500/10 shadow-lg'
        : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
    }`}>
      <span className={`w-1.5 h-1.5 rounded-full ${active ? 'bg-green-400 animate-pulse' : 'bg-gray-500'}`} />
      {label}
    </span>
  );
}

function Card({ children, className = '', hover = false }) {
  return (
    <div className={`
      bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl
      p-4 sm:p-6
      transition-all duration-300
      ${hover ? 'hover:bg-white/8 hover:border-white/20 hover:shadow-xl hover:shadow-black/20 hover:-translate-y-0.5' : ''}
      ${className}
    `}>
      {children}
    </div>
  );
}

function Button({ children, onClick, variant = 'primary', disabled = false, loading = false, size = 'default', fullWidth = false }) {
  const variants = {
    primary: 'bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-black shadow-lg shadow-amber-500/20 hover:shadow-amber-500/30',
    secondary: 'bg-white/10 hover:bg-white/20 text-white border border-white/20 hover:border-white/30',
    danger: 'bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30 hover:border-red-500/50',
    success: 'bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/30 hover:border-green-500/50',
    ghost: 'bg-transparent hover:bg-white/10 text-gray-400 hover:text-white'
  };

  const sizes = {
    small: 'px-2.5 py-1.5 text-xs sm:text-sm',
    default: 'px-3 py-2 sm:px-4 sm:py-2.5 text-sm',
    large: 'px-5 py-3 sm:px-6 sm:py-3.5 text-base'
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`
        ${sizes[size]} rounded-lg font-medium
        transition-all duration-200
        flex items-center justify-center gap-2
        active:scale-[0.98]
        ${variants[variant]}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        ${fullWidth ? 'w-full' : ''}
      `}
    >
      {loading && <RefreshCw className="w-4 h-4 animate-spin" />}
      {children}
    </button>
  );
}

function StatCard({ icon: Icon, label, value, subtext, trend }) {
  return (
    <Card hover>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-gray-400 text-xs sm:text-sm truncate">{label}</p>
          <p className="text-2xl sm:text-3xl font-bold text-white mt-1 truncate">{value}</p>
          {subtext && <p className="text-gray-500 text-xs sm:text-sm mt-1 truncate">{subtext}</p>}
          {trend && (
            <p className={`text-xs mt-2 flex items-center gap-1 ${trend > 0 ? 'text-green-400' : 'text-red-400'}`}>
              <ChevronRight className={`w-3 h-3 ${trend > 0 ? 'rotate-[-90deg]' : 'rotate-90'}`} />
              {Math.abs(trend)}% from last week
            </p>
          )}
        </div>
        <div className="p-2.5 sm:p-3 bg-gradient-to-br from-amber-500/20 to-amber-600/10 rounded-xl flex-shrink-0">
          <Icon className="w-5 h-5 sm:w-6 sm:h-6 text-amber-400" />
        </div>
      </div>
    </Card>
  );
}

// Media Preview Modal (supports both image and video)
function MediaModal({ mediaUrl, mediaType, onClose }) {
  if (!mediaUrl) return null;

  return (
    <div
      className="fixed inset-0 bg-black/90 backdrop-blur-md z-50 flex items-center justify-center p-2 sm:p-4"
      onClick={onClose}
    >
      <div className="relative w-full max-w-4xl max-h-[95vh] sm:max-h-[90vh]">
        <button
          onClick={onClose}
          className="absolute -top-2 -right-2 sm:-top-10 sm:right-0 z-10 bg-black/50 sm:bg-transparent rounded-full p-2 text-white hover:text-amber-400 transition-colors"
        >
          <X className="w-6 h-6 sm:w-8 sm:h-8" />
        </button>
        {mediaType === 'video' ? (
          <video 
            src={mediaUrl}
            controls
            autoPlay
            loop
            className="max-w-full max-h-[85vh] rounded-lg shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          />
        ) : (
          <img 
            src={mediaUrl} 
            alt="Post preview" 
            className="max-w-full max-h-[85vh] object-contain rounded-lg shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          />
        )}
      </div>
    </div>
  );
}

// ============== Tab Components ==============

function OverviewTab({ status, onRefresh, onStartScheduler, onStopScheduler, onPostNow, loading }) {
  const scheduler = status?.scheduler || {};
  const queue = status?.queue || {};
  const linkedin = status?.linkedin || {};

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <StatCard
          icon={FileText}
          label="Queue Size"
          value={queue.pending || 0}
          subtext="Posts waiting"
        />
        <StatCard
          icon={Send}
          label="Published Today"
          value={queue.published_today || 0}
          subtext="Posts sent"
        />
        <StatCard
          icon={BarChart3}
          label="This Week"
          value={queue.published_this_week || 0}
          subtext="Total published"
        />
        <StatCard
          icon={Zap}
          label="Scheduler"
          value={scheduler.running ? 'Active' : 'Stopped'}
          subtext={scheduler.running ? 'Auto-posting' : 'Manual mode'}
        />
      </div>

      {/* Control Panel */}
      <Card>
        <h3 className="text-base sm:text-lg font-semibold text-white mb-3 sm:mb-4">Control Panel</h3>
        <div className="grid grid-cols-2 sm:flex sm:flex-wrap gap-2 sm:gap-3">
          {scheduler.running ? (
            <Button onClick={onStopScheduler} variant="danger" loading={loading} fullWidth className="sm:w-auto">
              <Square className="w-4 h-4" /> <span className="hidden xs:inline">Stop</span> Scheduler
            </Button>
          ) : (
            <Button onClick={onStartScheduler} variant="success" loading={loading} fullWidth className="sm:w-auto">
              <Play className="w-4 h-4" /> <span className="hidden xs:inline">Start</span> Scheduler
            </Button>
          )}
          <Button onClick={onPostNow} variant="primary" loading={loading} fullWidth className="sm:w-auto">
            <Send className="w-4 h-4" /> Post Now
          </Button>
          <Button onClick={onRefresh} variant="secondary" loading={loading} fullWidth className="col-span-2 sm:w-auto sm:col-span-1">
            <RefreshCw className="w-4 h-4" /> Refresh
          </Button>
        </div>
      </Card>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
        {/* Schedule Info */}
        <Card hover>
          <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
            <div className="p-2 bg-amber-500/20 rounded-lg">
              <Clock className="w-4 h-4 sm:w-5 sm:h-5 text-amber-400" />
            </div>
            <h3 className="text-base sm:text-lg font-semibold text-white">Schedule</h3>
          </div>
          <div className="space-y-2 text-sm sm:text-base text-gray-300">
            <div className="flex justify-between items-center py-1.5 border-b border-white/5">
              <span>Daily at</span>
              <span className="text-white font-medium">
                {String(scheduler.schedule?.hour || 9).padStart(2, '0')}:
                {String(scheduler.schedule?.minute || 0).padStart(2, '0')}
              </span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b border-white/5">
              <span>Timezone</span>
              <span className="text-white font-medium text-xs sm:text-sm">
                {scheduler.schedule?.timezone || 'America/New_York'}
              </span>
            </div>
            {scheduler.next_run && (
              <div className="flex justify-between items-center py-1.5">
                <span>Next run</span>
                <span className="text-amber-400 font-medium text-xs sm:text-sm">
                  {new Date(scheduler.next_run).toLocaleString()}
                </span>
              </div>
            )}
          </div>
        </Card>

        {/* LinkedIn Status */}
        <Card hover>
          <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <Linkedin className="w-4 h-4 sm:w-5 sm:h-5 text-blue-400" />
            </div>
            <h3 className="text-base sm:text-lg font-semibold text-white">LinkedIn</h3>
          </div>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
              {linkedin.configured ? (
                <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
              ) : (
                <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0" />
              )}
              <div>
                <span className="text-white font-medium block">
                  {linkedin.configured ? 'Connected' : 'Not configured'}
                </span>
                <span className="text-gray-400 text-xs">
                  {linkedin.configured ? 'Ready to post' : 'Set up required'}
                </span>
              </div>
            </div>
            {linkedin.mock && (
              <div className="flex items-center gap-2 text-yellow-400 text-sm bg-yellow-500/10 rounded-lg p-2">
                <AlertCircle className="w-4 h-4" />
                Mock mode enabled
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}

function ScheduleTab({ status, onSetSchedule, loading }) {
  const [hour, setHour] = useState(9);
  const [minute, setMinute] = useState(0);
  const [timezone, setTimezone] = useState('America/New_York');

  useEffect(() => {
    if (status?.scheduler?.schedule) {
      setHour(status.scheduler.schedule.hour || 9);
      setMinute(status.scheduler.schedule.minute || 0);
      setTimezone(status.scheduler.schedule.timezone || 'America/New_York');
    }
  }, [status]);

  const handleSave = () => {
    onSetSchedule({ hour, minute, timezone });
  };

  return (
    <div className="space-y-4 sm:space-y-6">
      <Card>
        <div className="flex items-center gap-3 mb-4 sm:mb-6">
          <div className="p-2 bg-amber-500/20 rounded-lg">
            <Clock className="w-5 h-5 text-amber-400" />
          </div>
          <h3 className="text-base sm:text-lg font-semibold text-white">Daily Post Schedule</h3>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-6">
          <div>
            <label className="block text-gray-400 text-xs sm:text-sm mb-1.5 sm:mb-2">Hour (0-23)</label>
            <input
              type="number"
              min="0"
              max="23"
              value={hour}
              onChange={(e) => setHour(parseInt(e.target.value))}
              className="w-full bg-white/5 border border-white/20 rounded-lg px-3 sm:px-4 py-2.5 sm:py-2 text-white text-base focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-500/20 transition-all"
            />
          </div>
          <div>
            <label className="block text-gray-400 text-xs sm:text-sm mb-1.5 sm:mb-2">Minute (0-59)</label>
            <input
              type="number"
              min="0"
              max="59"
              value={minute}
              onChange={(e) => setMinute(parseInt(e.target.value))}
              className="w-full bg-white/5 border border-white/20 rounded-lg px-3 sm:px-4 py-2.5 sm:py-2 text-white text-base focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-500/20 transition-all"
            />
          </div>
          <div className="col-span-2 sm:col-span-1">
            <label className="block text-gray-400 text-xs sm:text-sm mb-1.5 sm:mb-2">Timezone</label>
            <select
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="w-full bg-white/5 border border-white/20 rounded-lg px-3 sm:px-4 py-2.5 sm:py-2 text-white text-base focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-500/20 transition-all appearance-none cursor-pointer"
            >
              <option value="America/New_York">Eastern (New York)</option>
              <option value="America/Chicago">Central (Chicago)</option>
              <option value="America/Denver">Mountain (Denver)</option>
              <option value="America/Los_Angeles">Pacific (Los Angeles)</option>
              <option value="UTC">UTC</option>
            </select>
          </div>
        </div>

        <div className="mt-4 sm:mt-6 pt-4 border-t border-white/10">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
            <div className="bg-amber-500/10 rounded-lg p-3 flex-1">
              <p className="text-gray-300 text-sm">
                Posts will be published daily at{' '}
                <span className="text-amber-400 font-semibold">
                  {String(hour).padStart(2, '0')}:{String(minute).padStart(2, '0')}
                </span>{' '}
                <span className="text-gray-400 text-xs block sm:inline mt-1 sm:mt-0">
                  ({timezone})
                </span>
              </p>
            </div>
            <Button onClick={handleSave} variant="primary" loading={loading} fullWidth className="sm:w-auto">
              <Calendar className="w-4 h-4" /> Save Schedule
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

function QueueTab({ queue, onGenerate, onRemove, onPostNow, loading }) {
  const posts = queue?.posts || [];
  const [selectedMedia, setSelectedMedia] = useState(null);
  const [selectedMediaType, setSelectedMediaType] = useState('image');
  const [useVideo, setUseVideo] = useState(false);
  const [numPosts, setNumPosts] = useState(1);

  // Helper to safely render the cultural reference
  const renderCulturalReference = (ref) => {
    if (!ref) return null;
    if (typeof ref === 'string') return ref;
    return ref.reference || ref.source || ref.context || 'Unknown reference';
  };

  // Handle media preview click
  const handleMediaClick = (post) => {
    const isVideo = post.media_type === 'video' || post.image_url?.includes('/videos/') || post.image_url?.endsWith('.mp4');
    if (isVideo) {
      setSelectedMedia(getVideoUrl(post.image_url));
      setSelectedMediaType('video');
    } else {
      setSelectedMedia(getImageUrl(post.image_url));
      setSelectedMediaType('image');
    }
  };

  // Calculate estimated cost
  const estimatedCost = useVideo
    ? (numPosts * 1.05).toFixed(2)
    : (numPosts * 0.08).toFixed(2);

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Media Modal */}
      {selectedMedia && (
        <MediaModal
          mediaUrl={selectedMedia}
          mediaType={selectedMediaType}
          onClose={() => setSelectedMedia(null)}
        />
      )}

      {/* Generate Controls */}
      <Card>
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-amber-500/20 rounded-lg">
            <Sparkles className="w-5 h-5 text-amber-400" />
          </div>
          <h3 className="text-base sm:text-lg font-semibold text-white">Generate Content</h3>
        </div>

        <div className="space-y-4">
          {/* Controls row */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Number of posts */}
            <div className="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-2 border border-white/10">
              <label className="text-gray-400 text-xs sm:text-sm">Posts:</label>
              <select
                value={numPosts}
                onChange={(e) => setNumPosts(parseInt(e.target.value))}
                className="bg-transparent text-white text-sm focus:outline-none cursor-pointer"
              >
                {[1, 2, 3, 4, 5].map(n => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </div>

            {/* Video toggle */}
            <label className="flex items-center gap-2 cursor-pointer bg-white/5 rounded-lg px-3 py-2 border border-white/10 transition-all hover:bg-white/10">
              <input
                type="checkbox"
                checked={useVideo}
                onChange={(e) => setUseVideo(e.target.checked)}
                className="w-4 h-4 rounded border-gray-500 text-amber-500 focus:ring-amber-500 focus:ring-offset-0 bg-white/10"
              />
              <span className="text-xs sm:text-sm text-gray-300 flex items-center gap-1.5">
                {useVideo ? <Video className="w-4 h-4 text-purple-400" /> : <Image className="w-4 h-4 text-blue-400" />}
                <span className="hidden xs:inline">{useVideo ? 'Video' : 'Image'}</span>
              </span>
              <span className={`text-xs px-2 py-0.5 rounded-full ${
                useVideo
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                  : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
              }`}>
                {useVideo ? '~$1' : '$0.03'}
              </span>
            </label>

            {/* Generate button */}
            <Button
              onClick={() => onGenerate(numPosts, useVideo)}
              variant="primary"
              loading={loading}
              className="flex-1 sm:flex-none"
            >
              <Sparkles className="w-4 h-4" />
              <span className="hidden sm:inline">Generate</span> {useVideo ? 'Video' : 'Image'}
            </Button>
          </div>

          {/* Video info banner */}
          {useVideo && (
            <div className="p-3 bg-purple-500/10 border border-purple-500/20 rounded-lg">
              <p className="text-purple-300 text-xs sm:text-sm flex items-start sm:items-center gap-2">
                <Video className="w-4 h-4 flex-shrink-0 mt-0.5 sm:mt-0" />
                <span>
                  <strong>Video mode:</strong> 8-second cinematic video with Veo 3.1 Fast •
                  Est. cost: <strong>${estimatedCost}</strong>
                </span>
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* Queue List Header */}
      <div className="flex justify-between items-center px-1">
        <h3 className="text-base sm:text-lg font-semibold text-white flex items-center gap-2">
          <FileText className="w-4 h-4 sm:w-5 sm:h-5 text-gray-400" />
          Post Queue
          <span className="text-sm font-normal text-gray-400">({posts.length})</span>
        </h3>
      </div>

      {posts.length === 0 ? (
        <Card>
          <div className="text-center py-8 sm:py-12">
            <div className="w-16 h-16 sm:w-20 sm:h-20 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4">
              <FileText className="w-8 h-8 sm:w-10 sm:h-10 text-gray-600" />
            </div>
            <p className="text-gray-400 font-medium">Queue is empty</p>
            <p className="text-gray-500 text-sm mt-1">Generate content to add posts to the queue</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-3 sm:space-y-4">
          {posts.map((post, index) => {
            const isVideo = post.media_type === 'video' || post.image_url?.includes('/videos/') || post.image_url?.endsWith('.mp4');
            const mediaUrl = isVideo ? getVideoUrl(post.image_url) : getImageUrl(post.image_url);

            return (
              <Card key={post.id || index} hover>
                <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                  {/* Media Preview */}
                  {mediaUrl && (
                    <div
                      className="flex-shrink-0 w-full sm:w-28 md:w-36 lg:w-40 h-40 sm:h-28 md:h-36 lg:h-40 relative group cursor-pointer rounded-lg overflow-hidden"
                      onClick={() => handleMediaClick(post)}
                    >
                      {isVideo ? (
                        <>
                          <video
                            src={mediaUrl}
                            className="w-full h-full object-cover"
                            muted
                            onError={(e) => {
                              e.target.style.display = 'none';
                              e.target.nextSibling.style.display = 'flex';
                            }}
                          />
                          <div
                            className="hidden w-full h-full bg-white/5 items-center justify-center"
                          >
                            <Video className="w-8 h-8 text-gray-500" />
                          </div>
                          {/* Play icon overlay */}
                          <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                            <div className="w-10 h-10 sm:w-12 sm:h-12 bg-black/60 rounded-full flex items-center justify-center backdrop-blur-sm">
                              <Play className="w-5 h-5 sm:w-6 sm:h-6 text-white ml-0.5" />
                            </div>
                          </div>
                        </>
                      ) : (
                        <>
                          <img
                            src={mediaUrl}
                            alt="Post image"
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.target.style.display = 'none';
                              e.target.nextSibling.style.display = 'flex';
                            }}
                          />
                          <div
                            className="hidden w-full h-full bg-white/5 items-center justify-center"
                          >
                            <Image className="w-8 h-8 text-gray-500" />
                          </div>
                        </>
                      )}
                      {/* Zoom overlay */}
                      <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                        <ZoomIn className="w-6 h-6 sm:w-8 sm:h-8 text-white" />
                      </div>
                    </div>
                  )}

                  {/* Content */}
                  <div className="flex-1 min-w-0 flex flex-col">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <StatusBadge active={post.status === 'pending'} label={post.status} />
                      {post.image_url && (
                        <span className={`text-xs sm:text-sm flex items-center gap-1 ${isVideo ? 'text-purple-400' : 'text-blue-400'}`}>
                          {isVideo ? <Video className="w-3 h-3 sm:w-4 sm:h-4" /> : <Image className="w-3 h-3 sm:w-4 sm:h-4" />}
                          <span className="hidden xs:inline">{isVideo ? 'Video' : 'Image'}</span>
                        </span>
                      )}
                      {(post.validation_score || post.average_score) && (
                        <span className="text-amber-400 text-xs sm:text-sm flex items-center gap-1">
                          <Zap className="w-3 h-3" />
                          {(post.validation_score || post.average_score).toFixed(1)}/10
                        </span>
                      )}
                    </div>

                    {/* Post content */}
                    <p className="text-gray-300 text-sm sm:text-base leading-relaxed mb-2 line-clamp-3 sm:line-clamp-none">
                      {post.content}
                    </p>

                    {post.hashtags?.length > 0 && (
                      <p className="text-amber-400 text-xs sm:text-sm truncate">
                        {post.hashtags.map(h => h.startsWith('#') ? h : `#${h}`).join(' ')}
                      </p>
                    )}
                    {post.cultural_reference && (
                      <p className="text-purple-400 text-xs mt-2 truncate">
                        📺 {renderCulturalReference(post.cultural_reference)}
                      </p>
                    )}

                    {/* Actions - moved to bottom on mobile */}
                    <div className="flex gap-2 mt-3 pt-3 border-t border-white/5 sm:border-0 sm:mt-auto sm:pt-0">
                      {post.status === 'pending' && (
                        <Button onClick={() => onPostNow(post.id)} disabled={loading} size="small" fullWidth className="sm:w-auto">
                          <Send className="w-3.5 h-3.5" />
                          <span className="sm:hidden">Post</span>
                          <span className="hidden sm:inline">Post Now</span>
                        </Button>
                      )}
                      <Button onClick={() => onRemove(post.id)} variant="danger" size="small" fullWidth className="sm:w-auto">
                        <X className="w-3.5 h-3.5" />
                        Remove
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

function HistoryTab({ history }) {
  const posts = history?.posts || [];
  const [selectedMedia, setSelectedMedia] = useState(null);
  const [selectedMediaType, setSelectedMediaType] = useState('image');

  const handleMediaClick = (post) => {
    const isVideo = post.media_type === 'video' || post.image_url?.includes('/videos/') || post.image_url?.endsWith('.mp4');
    if (isVideo) {
      setSelectedMedia(getVideoUrl(post.image_url));
      setSelectedMediaType('video');
    } else {
      setSelectedMedia(getImageUrl(post.image_url));
      setSelectedMediaType('image');
    }
  };

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Media Modal */}
      {selectedMedia && (
        <MediaModal
          mediaUrl={selectedMedia}
          mediaType={selectedMediaType}
          onClose={() => setSelectedMedia(null)}
        />
      )}

      {/* Header */}
      <div className="flex items-center gap-3 px-1">
        <History className="w-5 h-5 text-gray-400" />
        <h3 className="text-base sm:text-lg font-semibold text-white">Published Posts</h3>
        <span className="text-sm text-gray-500">({posts.length})</span>
      </div>

      {posts.length === 0 ? (
        <Card>
          <div className="text-center py-8 sm:py-12">
            <div className="w-16 h-16 sm:w-20 sm:h-20 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4">
              <History className="w-8 h-8 sm:w-10 sm:h-10 text-gray-600" />
            </div>
            <p className="text-gray-400 font-medium">No posts published yet</p>
            <p className="text-gray-500 text-sm mt-1">Published posts will appear here</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-3 sm:space-y-4">
          {posts.map((post, index) => {
            const isVideo = post.media_type === 'video' || post.image_url?.includes('/videos/') || post.image_url?.endsWith('.mp4');
            const mediaUrl = isVideo ? getVideoUrl(post.image_url) : getImageUrl(post.image_url);

            return (
              <Card key={post.id || index} hover>
                <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                  {/* Media Preview */}
                  {mediaUrl && (
                    <div
                      className="flex-shrink-0 w-full sm:w-20 md:w-24 h-32 sm:h-20 md:h-24 relative group cursor-pointer rounded-lg overflow-hidden"
                      onClick={() => handleMediaClick(post)}
                    >
                      {isVideo ? (
                        <>
                          <video
                            src={mediaUrl}
                            className="w-full h-full object-cover"
                            muted
                            onError={(e) => { e.target.style.display = 'none'; }}
                          />
                          <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                            <div className="w-10 h-10 sm:w-8 sm:h-8 bg-black/60 rounded-full flex items-center justify-center backdrop-blur-sm">
                              <Play className="w-5 h-5 sm:w-4 sm:h-4 text-white ml-0.5" />
                            </div>
                          </div>
                        </>
                      ) : (
                        <img
                          src={mediaUrl}
                          alt="Post image"
                          className="w-full h-full object-cover"
                          onError={(e) => { e.target.style.display = 'none'; }}
                        />
                      )}
                      <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                        <ZoomIn className="w-6 h-6 text-white" />
                      </div>
                    </div>
                  )}

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start gap-2 sm:gap-3">
                      {post.status === 'success' ? (
                        <div className="p-1.5 bg-green-500/20 rounded-full flex-shrink-0">
                          <CheckCircle className="w-4 h-4 text-green-400" />
                        </div>
                      ) : (
                        <div className="p-1.5 bg-red-500/20 rounded-full flex-shrink-0">
                          <AlertCircle className="w-4 h-4 text-red-400" />
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-2">
                          <span className="text-gray-400 text-xs sm:text-sm">
                            {new Date(post.published_at).toLocaleDateString()} {new Date(post.published_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                          </span>
                          {post.linkedin_post_id && (
                            <span className="text-blue-400 text-xs bg-blue-500/10 px-2 py-0.5 rounded-full truncate max-w-[120px] sm:max-w-none">
                              {post.linkedin_post_id}
                            </span>
                          )}
                          {isVideo && (
                            <span className="text-purple-400 text-xs flex items-center gap-1 bg-purple-500/10 px-2 py-0.5 rounded-full">
                              <Video className="w-3 h-3" /> Video
                            </span>
                          )}
                        </div>
                        <p className="text-gray-300 text-sm sm:text-base line-clamp-2 sm:line-clamp-none">{post.content}</p>
                        {post.error_message && (
                          <p className="text-red-400 text-xs sm:text-sm mt-2 bg-red-500/10 p-2 rounded-lg">{post.error_message}</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ============== Comments Tab (NEW - Comment Engagement System) ==============

function CommentsTab() {
  const [comments, setComments] = useState([]);
  const [summary, setSummary] = useState({});
  const [showGenerator, setShowGenerator] = useState(false);
  const [postUrl, setPostUrl] = useState('');
  const [postContent, setPostContent] = useState('');
  const [authorName, setAuthorName] = useState('');
  const [generating, setGenerating] = useState(false);
  const [localLoading, setLocalLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [selectedComment, setSelectedComment] = useState(null);
  const [copiedId, setCopiedId] = useState(null);
  const [activeSubTab, setActiveSubTab] = useState('queue'); // queue, history

  const showLocalMessage = (msg) => {
    setMessage(msg);
    setTimeout(() => setMessage(null), 3000);
  };

  // Fetch comments
  const fetchComments = useCallback(async () => {
    setLocalLoading(true);
    try {
      const endpoint = activeSubTab === 'history' 
        ? '/api/comments/history?limit=50&include_rejected=true'
        : '/api/comments/queue?limit=50';
      const data = await api.get(endpoint);
      setComments(data.comments || []);
      if (data.summary) setSummary(data.summary);
    } catch (err) {
      console.error('Failed to fetch comments:', err);
    }
    setLocalLoading(false);
  }, [activeSubTab]);

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  // Generate comments for a post
  const handleGenerate = async () => {
    if (!postUrl || !postContent) {
      showLocalMessage('❌ Please provide both URL and content');
      return;
    }

    setGenerating(true);
    showLocalMessage('🔄 Generating comment options...');
    
    try {
      const result = await api.post('/api/comments/generate', {
        post_url: postUrl,
        post_content: postContent,
        author_name: authorName || 'Unknown',
        num_options: 3
      });
      
      showLocalMessage(`✅ Generated ${result.comment?.comment_options?.length || 3} comment options`);
      setShowGenerator(false);
      setPostUrl('');
      setPostContent('');
      setAuthorName('');
      await fetchComments();
    } catch (err) {
      showLocalMessage(`❌ Failed: ${err.message}`);
    }
    setGenerating(false);
  };

  // Select an option
  const handleSelectOption = async (commentId, optionId) => {
    try {
      await api.patch(`/api/comments/${commentId}/select?option_id=${optionId}`);
      showLocalMessage('✅ Option selected');
      await fetchComments();
    } catch (err) {
      showLocalMessage(`❌ Failed: ${err.message}`);
    }
  };

  // Approve a comment
  const handleApprove = async (commentId, postImmediately = false) => {
    try {
      await api.patch(`/api/comments/${commentId}/approve`, {
        approved_by: 'admin',
        post_immediately: postImmediately
      });
      showLocalMessage(postImmediately ? '✅ Approved and posting...' : '✅ Comment approved');
      await fetchComments();
    } catch (err) {
      showLocalMessage(`❌ Failed: ${err.message}`);
    }
  };

  // Reject a comment
  const handleReject = async (commentId) => {
    try {
      await api.patch(`/api/comments/${commentId}/reject`);
      showLocalMessage('✅ Comment rejected');
      await fetchComments();
    } catch (err) {
      showLocalMessage(`❌ Failed: ${err.message}`);
    }
  };

  // Post an approved comment
  const handlePost = async (commentId) => {
    try {
      await api.post(`/api/comments/${commentId}/post`);
      showLocalMessage('✅ Comment posted to LinkedIn!');
      await fetchComments();
    } catch (err) {
      showLocalMessage(`❌ Failed: ${err.message}`);
    }
  };

  // Delete a comment
  const handleDelete = async (commentId) => {
    try {
      await api.delete(`/api/comments/${commentId}`);
      showLocalMessage('✅ Comment deleted');
      await fetchComments();
    } catch (err) {
      showLocalMessage(`❌ Failed: ${err.message}`);
    }
  };

  // Copy to clipboard
  const handleCopy = async (text, id) => {
    await navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getStyleColor = (style) => {
    const colors = {
      knowing_nod: 'text-blue-400 bg-blue-500/20 border-blue-500/30',
      absurdist_tangent: 'text-purple-400 bg-purple-500/20 border-purple-500/30',
      human_moment: 'text-green-400 bg-green-500/20 border-green-500/30',
      witty_insight: 'text-amber-400 bg-amber-500/20 border-amber-500/30',
      warm_encouragement: 'text-pink-400 bg-pink-500/20 border-pink-500/30'
    };
    return colors[style] || 'text-gray-400 bg-gray-500/20 border-gray-500/30';
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30',
      approved: 'text-blue-400 bg-blue-500/20 border-blue-500/30',
      posted: 'text-green-400 bg-green-500/20 border-green-500/30',
      rejected: 'text-red-400 bg-red-500/20 border-red-500/30',
      failed: 'text-red-400 bg-red-500/20 border-red-500/30'
    };
    return colors[status] || 'text-gray-400 bg-gray-500/20 border-gray-500/30';
  };

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Local Message Toast */}
      {message && (
        <div className="fixed top-16 sm:top-20 right-2 sm:right-6 left-2 sm:left-auto z-50 animate-slide-in">
          <div className="bg-gray-800/95 backdrop-blur-sm border border-white/20 rounded-xl px-4 py-3 shadow-2xl max-w-sm mx-auto sm:mx-0">
            <p className="text-white text-sm sm:text-base">{message}</p>
          </div>
        </div>
      )}

      {/* Stats Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
        <StatCard icon={MessageCircle} label="Pending" value={summary.pending || 0} />
        <StatCard icon={CheckCircle} label="Approved" value={summary.approved || 0} />
        <StatCard icon={Send} label="Posted" value={summary.posted || 0} />
        <StatCard icon={ThumbsUp} label="Total Likes" value={summary.total_likes || 0} />
      </div>

      {/* Controls */}
      <Card>
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveSubTab('queue')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeSubTab === 'queue'
                  ? 'bg-amber-500 text-black'
                  : 'bg-white/10 text-gray-300 hover:bg-white/20'
              }`}
            >
              Queue
            </button>
            <button
              onClick={() => setActiveSubTab('history')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeSubTab === 'history'
                  ? 'bg-amber-500 text-black'
                  : 'bg-white/10 text-gray-300 hover:bg-white/20'
              }`}
            >
              History
            </button>
          </div>
          <div className="flex gap-2 w-full sm:w-auto">
            <Button onClick={fetchComments} variant="secondary" loading={localLoading}>
              <RefreshCw className="w-4 h-4" />
              <span className="hidden sm:inline">Refresh</span>
            </Button>
            <Button onClick={() => setShowGenerator(true)} variant="primary">
              <Sparkles className="w-4 h-4" />
              <span className="hidden sm:inline">New Comment</span>
              <span className="sm:hidden">New</span>
            </Button>
          </div>
        </div>
      </Card>

      {/* Generator Modal */}
      {showGenerator && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-md z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
          <Card className="w-full sm:max-w-2xl max-h-[85vh] sm:max-h-[90vh] overflow-y-auto rounded-t-2xl sm:rounded-xl">
            <div className="flex justify-between items-center mb-4 sticky top-0 bg-inherit pb-2">
              <h3 className="text-base sm:text-lg font-semibold text-white">Generate Comment</h3>
              <button onClick={() => setShowGenerator(false)} className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors">
                <X className="w-5 h-5 sm:w-6 sm:h-6" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs sm:text-sm text-gray-400 mb-1.5">LinkedIn Post URL *</label>
                <input
                  type="url"
                  value={postUrl}
                  onChange={(e) => setPostUrl(e.target.value)}
                  placeholder="https://www.linkedin.com/feed/update/..."
                  className="w-full bg-white/5 border border-white/20 rounded-lg px-3 sm:px-4 py-2.5 sm:py-2 text-white text-base placeholder-gray-500 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-500/20"
                />
              </div>

              <div>
                <label className="block text-xs sm:text-sm text-gray-400 mb-1.5">Post Content *</label>
                <textarea
                  value={postContent}
                  onChange={(e) => setPostContent(e.target.value)}
                  placeholder="Paste the post content here..."
                  rows={5}
                  className="w-full bg-white/5 border border-white/20 rounded-lg px-3 sm:px-4 py-2.5 sm:py-2 text-white text-base placeholder-gray-500 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-500/20 resize-none"
                />
              </div>

              <div>
                <label className="block text-xs sm:text-sm text-gray-400 mb-1.5">Author Name</label>
                <input
                  type="text"
                  value={authorName}
                  onChange={(e) => setAuthorName(e.target.value)}
                  placeholder="Post author's name"
                  className="w-full bg-white/5 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:border-amber-500 focus:outline-none"
                />
              </div>
              
              <div className="flex gap-3 pt-2">
                <Button onClick={() => setShowGenerator(false)} variant="secondary">
                  Cancel
                </Button>
                <Button onClick={handleGenerate} variant="primary" loading={generating}>
                  <Sparkles className="w-4 h-4" /> Generate Options
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Comments List */}
      {comments.length === 0 ? (
        <Card>
          <div className="text-center py-8">
            <MessageCircle className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No comments in {activeSubTab}</p>
            <p className="text-gray-500 text-sm mt-1">
              {activeSubTab === 'queue' ? 'Generate a comment to get started' : 'Posted comments will appear here'}
            </p>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          {comments.map((comment) => (
            <Card key={comment.id} className="overflow-hidden">
              {/* Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(comment.status)}`}>
                    {comment.status}
                  </span>
                  <span className="text-gray-500 text-sm">
                    {comment.source_post?.author_name || 'Unknown'}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {comment.source_post?.url && (
                    <a
                      href={comment.source_post.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 text-sm flex items-center gap-1"
                    >
                      <ExternalLink className="w-4 h-4" />
                      <span className="hidden sm:inline">View Post</span>
                    </a>
                  )}
                  {comment.engagement && (
                    <div className="flex items-center gap-3 text-sm">
                      <span className="text-gray-400 flex items-center gap-1">
                        <ThumbsUp className="w-4 h-4" /> {comment.engagement.likes}
                      </span>
                      <span className="text-gray-400 flex items-center gap-1">
                        <MessageSquare className="w-4 h-4" /> {comment.engagement.replies}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Source Post Preview */}
              <div className="bg-white/5 rounded-lg p-3 mb-4">
                <p className="text-gray-400 text-sm line-clamp-3">{comment.source_post?.content}</p>
                {comment.source_post?.topic && (
                  <span className="inline-block mt-2 text-xs text-gray-500">
                    Topic: {comment.source_post.topic}
                  </span>
                )}
              </div>

              {/* Comment Options */}
              {comment.comment_options && comment.comment_options.length > 0 && (
                <div className="space-y-3 mb-4">
                  <p className="text-sm font-medium text-gray-300">Generated Options:</p>
                  {comment.comment_options.map((option) => (
                    <div
                      key={option.id}
                      className={`p-3 rounded-lg border transition-colors ${
                        comment.selected_option_id === option.id
                          ? 'bg-amber-500/10 border-amber-500/50'
                          : 'bg-white/5 border-white/10 hover:border-white/20'
                      }`}
                    >
                      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2 mb-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium border w-fit ${getStyleColor(option.style)}`}>
                          {option.style?.replace('_', ' ')}
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="text-amber-400 text-sm">
                            Score: {option.overall_score?.toFixed(1)}
                          </span>
                          <button
                            onClick={() => handleCopy(option.content, option.id)}
                            className="text-gray-400 hover:text-white p-1"
                            title="Copy to clipboard"
                          >
                            {copiedId === option.id ? (
                              <Check className="w-4 h-4 text-green-400" />
                            ) : (
                              <Copy className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                      </div>
                      <p className="text-white text-sm mb-2">{option.content}</p>
                      {option.reasoning && (
                        <p className="text-gray-500 text-xs">{option.reasoning}</p>
                      )}
                      {comment.status === 'pending' && comment.selected_option_id !== option.id && (
                        <button
                          onClick={() => handleSelectOption(comment.id, option.id)}
                          className="mt-2 text-sm text-amber-400 hover:text-amber-300"
                        >
                          Select this option
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Selected/Final Comment */}
              {comment.final_comment && (
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3 mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-green-400 text-sm font-medium">Selected Comment:</span>
                    <button
                      onClick={() => handleCopy(comment.final_comment, `final-${comment.id}`)}
                      className="text-gray-400 hover:text-white p-1"
                      title="Copy to clipboard"
                    >
                      {copiedId === `final-${comment.id}` ? (
                        <Check className="w-4 h-4 text-green-400" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                  <p className="text-white">{comment.final_comment}</p>
                </div>
              )}

              {/* Actions */}
              <div className="flex flex-wrap gap-2 pt-2 border-t border-white/10">
                {comment.status === 'pending' && (
                  <>
                    <Button onClick={() => handleApprove(comment.id)} variant="success" className="flex-1 sm:flex-none">
                      <CheckCircle className="w-4 h-4" />
                      <span className="hidden sm:inline">Approve</span>
                    </Button>
                    <Button onClick={() => handleApprove(comment.id, true)} variant="primary" className="flex-1 sm:flex-none">
                      <Send className="w-4 h-4" />
                      <span className="hidden sm:inline">Approve & Post</span>
                      <span className="sm:hidden">Post</span>
                    </Button>
                    <Button onClick={() => handleReject(comment.id)} variant="danger" className="flex-1 sm:flex-none">
                      <X className="w-4 h-4" />
                      <span className="hidden sm:inline">Reject</span>
                    </Button>
                  </>
                )}
                {comment.status === 'approved' && (
                  <Button onClick={() => handlePost(comment.id)} variant="primary">
                    <Send className="w-4 h-4" /> Post to LinkedIn
                  </Button>
                )}
                <Button onClick={() => handleDelete(comment.id)} variant="secondary" className="ml-auto">
                  Delete
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ============== Main App ==============

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [status, setStatus] = useState(null);
  const [queue, setQueue] = useState(null);
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);

  // Fetch data
  const fetchStatus = useCallback(async () => {
    try {
      const data = await api.get('/api/automation/status');
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(`Failed to connect: ${err.message}`);
    }
  }, []);

  const fetchQueue = useCallback(async () => {
    try {
      const data = await api.get('/api/automation/queue');
      setQueue(data);
    } catch (err) {
      console.error('Failed to fetch queue:', err);
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      const data = await api.get('/api/automation/history?limit=20');
      setHistory(data);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    await Promise.all([fetchStatus(), fetchQueue(), fetchHistory()]);
    setLoading(false);
  }, [fetchStatus, fetchQueue, fetchHistory]);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [refresh]);

  // Actions
  const showMessage = (msg, duration = 3000) => {
    setMessage(msg);
    setTimeout(() => setMessage(null), duration);
  };

  const handleStartScheduler = async () => {
    setLoading(true);
    try {
      await api.post('/api/automation/scheduler/start');
      showMessage('✅ Scheduler started');
      await refresh();
    } catch (err) {
      showMessage(`❌ Failed: ${err.message}`);
    }
    setLoading(false);
  };

  const handleStopScheduler = async () => {
    setLoading(true);
    try {
      await api.post('/api/automation/scheduler/stop');
      showMessage('✅ Scheduler stopped');
      await refresh();
    } catch (err) {
      showMessage(`❌ Failed: ${err.message}`);
    }
    setLoading(false);
  };

  const handlePostNow = async (postId = null) => {
    setLoading(true);
    try {
      const endpoint = postId
        ? `/api/automation/queue/post/${postId}`
        : '/api/automation/post-now';
      const response = await api.post(endpoint);
      const linkedinId = response.data?.linkedin_post_id;
      showMessage(`✅ Posted successfully!${linkedinId ? ' ID: ' + linkedinId : ''}`);
      await fetchQueue();
      await fetchHistory();
    } catch (err) {
      showMessage(`❌ Post failed: ${err.response?.data?.detail || err.message}`);
    }
    setLoading(false);
  };

  const handleSetSchedule = async (config) => {
    setLoading(true);
    try {
      await api.post('/api/automation/schedule', config);
      showMessage('✅ Schedule updated');
      await refresh();
    } catch (err) {
      showMessage(`❌ Failed: ${err.message}`);
    }
    setLoading(false);
  };

  // Updated to accept numPosts and useVideo
  const handleGenerate = async (numPosts = 1, useVideo = false) => {
    setLoading(true);
    const mediaType = useVideo ? 'video' : 'image';
    showMessage(`🔄 Generating ${numPosts} post${numPosts > 1 ? 's' : ''} with ${mediaType}...`);
    try {
      const result = await api.post('/api/automation/generate-content', { 
        num_posts: numPosts, 
        add_to_queue: true,
        use_video: useVideo
      });
      showMessage(`✅ Generated ${result.approved_posts} approved posts (${result.media_type || mediaType})`);
      await fetchQueue();
    } catch (err) {
      showMessage(`❌ Failed: ${err.message}`);
    }
    setLoading(false);
  };

  const handleRemoveFromQueue = async (postId) => {
    try {
      await api.delete(`/api/automation/queue/${postId}`);
      showMessage('✅ Post removed');
      await fetchQueue();
    } catch (err) {
      showMessage(`❌ Failed: ${err.message}`);
    }
  };

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'schedule', label: 'Schedule', icon: Calendar },
    { id: 'queue', label: 'Queue', icon: FileText },
    { id: 'comments', label: 'Comments', icon: MessageCircle },
    { id: 'history', label: 'History', icon: History },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex flex-col">
      {/* Header */}
      <header className="border-b border-white/10 bg-black/40 backdrop-blur-md sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="w-9 h-9 sm:w-10 sm:h-10 bg-gradient-to-br from-amber-400 to-amber-600 rounded-xl flex items-center justify-center shadow-lg shadow-amber-500/20">
                <Sparkles className="w-5 h-5 sm:w-6 sm:h-6 text-black" />
              </div>
              <div>
                <h1 className="text-lg sm:text-xl font-bold text-white">Jesse A. Eisenbalm</h1>
                <p className="text-gray-400 text-xs sm:text-sm hidden xs:block">Automation Dashboard</p>
              </div>
            </div>
            <div className="flex items-center gap-2 sm:gap-4">
              <StatusBadge
                active={status?.scheduler?.running}
                label={status?.scheduler?.running ? 'Running' : 'Stopped'}
              />
              {/* Mobile menu button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="sm:hidden p-2 text-gray-400 hover:text-white transition-colors"
              >
                <Menu className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-30 sm:hidden">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMobileMenuOpen(false)} />
          <div className="absolute top-[57px] left-0 right-0 bg-gray-900 border-b border-white/10 shadow-xl">
            <nav className="flex flex-col p-2">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveTab(tab.id);
                    setMobileMenuOpen(false);
                  }}
                  className={`px-4 py-3 flex items-center gap-3 rounded-lg transition-all ${
                    activeTab === tab.id
                      ? 'bg-amber-500/20 text-amber-400'
                      : 'text-gray-400 hover:bg-white/5 hover:text-white'
                  }`}
                >
                  <tab.icon className="w-5 h-5" />
                  {tab.label}
                  {activeTab === tab.id && <ChevronRight className="w-4 h-4 ml-auto" />}
                </button>
              ))}
            </nav>
          </div>
        </div>
      )}

      {/* Message Toast */}
      {message && (
        <div className="fixed top-16 sm:top-20 right-2 sm:right-6 left-2 sm:left-auto z-50 animate-slide-in">
          <div className="bg-gray-800/95 backdrop-blur-sm border border-white/20 rounded-xl px-4 py-3 shadow-2xl max-w-sm sm:max-w-md mx-auto sm:mx-0">
            <p className="text-white text-sm sm:text-base">{message}</p>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="bg-red-500/10 border-b border-red-500/30 px-4 sm:px-6 py-2 sm:py-3">
          <div className="max-w-7xl mx-auto flex items-center gap-2 sm:gap-3 text-red-400">
            <AlertCircle className="w-4 h-4 sm:w-5 sm:h-5 flex-shrink-0" />
            <span className="text-sm sm:text-base flex-1 truncate">{error}</span>
            <button onClick={refresh} className="text-xs sm:text-sm underline flex-shrink-0">Retry</button>
          </div>
        </div>
      )}

      {/* Desktop Tabs */}
      <div className="border-b border-white/10 hidden sm:block">
        <div className="max-w-7xl mx-auto px-6">
          <nav className="flex gap-1 overflow-x-auto scrollbar-hide">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-3 flex items-center gap-2 border-b-2 transition-all whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-amber-500 text-amber-400 bg-amber-500/5'
                    : 'border-transparent text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Mobile Tab Indicator */}
      <div className="sm:hidden border-b border-white/10 px-4 py-2">
        <div className="flex items-center gap-2 text-amber-400">
          {(() => {
            const currentTab = tabs.find(t => t.id === activeTab);
            return currentTab ? (
              <>
                <currentTab.icon className="w-4 h-4" />
                <span className="font-medium text-sm">{currentTab.label}</span>
              </>
            ) : null;
          })()}
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-8 w-full flex-1">
        {activeTab === 'overview' && (
          <OverviewTab
            status={status}
            onRefresh={refresh}
            onStartScheduler={handleStartScheduler}
            onStopScheduler={handleStopScheduler}
            onPostNow={handlePostNow}
            loading={loading}
          />
        )}
        {activeTab === 'schedule' && (
          <ScheduleTab
            status={status}
            onSetSchedule={handleSetSchedule}
            loading={loading}
          />
        )}
        {activeTab === 'queue' && (
          <QueueTab
            queue={queue}
            onGenerate={handleGenerate}
            onRemove={handleRemoveFromQueue}
            onPostNow={handlePostNow}
            loading={loading}
          />
        )}
        {activeTab === 'comments' && (
          <CommentsTab />
        )}
        {activeTab === 'history' && (
          <HistoryTab history={history} />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 py-4 sm:py-6 mt-auto bg-black/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 text-center">
          <p className="text-gray-500 text-xs sm:text-sm">
            <span className="text-amber-500/80 font-medium">Jesse A. Eisenbalm</span> Automation v2.0
          </p>
          <p className="text-gray-600 text-xs mt-1 hidden sm:block">
            "The only business lip balm that keeps you human in an AI world"
          </p>
        </div>
      </footer>
    </div>
  );
}