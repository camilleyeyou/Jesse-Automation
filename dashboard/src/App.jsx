import React, { useState, useEffect, useCallback } from 'react';
import { 
  Play, Square, Clock, Send, Sparkles, Calendar, 
  History, Settings, RefreshCw, AlertCircle, CheckCircle,
  Linkedin, Image, FileText, Zap, BarChart3, X, ZoomIn, Video
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
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
      active 
        ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
        : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
    }`}>
      {active ? '● ' : '○ '}{label}
    </span>
  );
}

function Card({ children, className = '' }) {
  return (
    <div className={`bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 ${className}`}>
      {children}
    </div>
  );
}

function Button({ children, onClick, variant = 'primary', disabled = false, loading = false }) {
  const variants = {
    primary: 'bg-amber-500 hover:bg-amber-400 text-black',
    secondary: 'bg-white/10 hover:bg-white/20 text-white border border-white/20',
    danger: 'bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30',
    success: 'bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/30'
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`px-4 py-2 rounded-lg font-medium transition-all flex items-center gap-2 
        ${variants[variant]} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      {loading && <RefreshCw className="w-4 h-4 animate-spin" />}
      {children}
    </button>
  );
}

function StatCard({ icon: Icon, label, value, subtext }) {
  return (
    <Card>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-400 text-sm">{label}</p>
          <p className="text-3xl font-bold text-white mt-1">{value}</p>
          {subtext && <p className="text-gray-500 text-sm mt-1">{subtext}</p>}
        </div>
        <div className="p-3 bg-amber-500/20 rounded-lg">
          <Icon className="w-6 h-6 text-amber-400" />
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
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div className="relative max-w-4xl max-h-[90vh]">
        <button 
          onClick={onClose}
          className="absolute -top-10 right-0 text-white hover:text-amber-400 transition-colors"
        >
          <X className="w-8 h-8" />
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
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
          subtext={scheduler.running ? 'Auto-posting enabled' : 'Manual mode'}
        />
      </div>

      {/* Control Panel */}
      <Card>
        <h3 className="text-lg font-semibold text-white mb-4">Control Panel</h3>
        <div className="flex flex-wrap gap-3">
          {scheduler.running ? (
            <Button onClick={onStopScheduler} variant="danger" loading={loading}>
              <Square className="w-4 h-4" /> Stop Scheduler
            </Button>
          ) : (
            <Button onClick={onStartScheduler} variant="success" loading={loading}>
              <Play className="w-4 h-4" /> Start Scheduler
            </Button>
          )}
          <Button onClick={onPostNow} variant="primary" loading={loading}>
            <Send className="w-4 h-4" /> Post Now
          </Button>
          <Button onClick={onRefresh} variant="secondary" loading={loading}>
            <RefreshCw className="w-4 h-4" /> Refresh
          </Button>
        </div>
      </Card>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Schedule Info */}
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <Clock className="w-5 h-5 text-amber-400" />
            <h3 className="text-lg font-semibold text-white">Schedule</h3>
          </div>
          <div className="space-y-2 text-gray-300">
            <p>Daily at: <span className="text-white font-medium">
              {String(scheduler.schedule?.hour || 9).padStart(2, '0')}:
              {String(scheduler.schedule?.minute || 0).padStart(2, '0')}
            </span></p>
            <p>Timezone: <span className="text-white font-medium">
              {scheduler.schedule?.timezone || 'America/New_York'}
            </span></p>
            {scheduler.next_run && (
              <p>Next run: <span className="text-amber-400 font-medium">
                {new Date(scheduler.next_run).toLocaleString()}
              </span></p>
            )}
          </div>
        </Card>

        {/* LinkedIn Status */}
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <Linkedin className="w-5 h-5 text-blue-400" />
            <h3 className="text-lg font-semibold text-white">LinkedIn</h3>
          </div>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              {linkedin.configured ? (
                <CheckCircle className="w-5 h-5 text-green-400" />
              ) : (
                <AlertCircle className="w-5 h-5 text-yellow-400" />
              )}
              <span className="text-gray-300">
                {linkedin.configured ? 'Connected' : 'Not configured'}
              </span>
            </div>
            {linkedin.mock && (
              <p className="text-yellow-400 text-sm">⚠️ Mock mode enabled</p>
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
    <div className="space-y-6">
      <Card>
        <h3 className="text-lg font-semibold text-white mb-6">Daily Post Schedule</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-gray-400 text-sm mb-2">Hour (0-23)</label>
            <input
              type="number"
              min="0"
              max="23"
              value={hour}
              onChange={(e) => setHour(parseInt(e.target.value))}
              className="w-full bg-white/5 border border-white/20 rounded-lg px-4 py-2 text-white focus:border-amber-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-gray-400 text-sm mb-2">Minute (0-59)</label>
            <input
              type="number"
              min="0"
              max="59"
              value={minute}
              onChange={(e) => setMinute(parseInt(e.target.value))}
              className="w-full bg-white/5 border border-white/20 rounded-lg px-4 py-2 text-white focus:border-amber-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-gray-400 text-sm mb-2">Timezone</label>
            <select
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="w-full bg-white/5 border border-white/20 rounded-lg px-4 py-2 text-white focus:border-amber-500 focus:outline-none"
            >
              <option value="America/New_York">Eastern (New York)</option>
              <option value="America/Chicago">Central (Chicago)</option>
              <option value="America/Denver">Mountain (Denver)</option>
              <option value="America/Los_Angeles">Pacific (Los Angeles)</option>
              <option value="UTC">UTC</option>
            </select>
          </div>
        </div>

        <div className="mt-6 flex items-center justify-between">
          <p className="text-gray-400">
            Posts will be published daily at{' '}
            <span className="text-amber-400 font-medium">
              {String(hour).padStart(2, '0')}:{String(minute).padStart(2, '0')}
            </span>{' '}
            {timezone}
          </p>
          <Button onClick={handleSave} variant="primary" loading={loading}>
            <Calendar className="w-4 h-4" /> Save Schedule
          </Button>
        </div>
      </Card>
    </div>
  );
}

function QueueTab({ queue, onGenerate, onRemove, loading }) {
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
    <div className="space-y-6">
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
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <h3 className="text-lg font-semibold text-white">Generate Content</h3>
          
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            {/* Number of posts */}
            <div className="flex items-center gap-2">
              <label className="text-gray-400 text-sm">Posts:</label>
              <select
                value={numPosts}
                onChange={(e) => setNumPosts(parseInt(e.target.value))}
                className="bg-white/5 border border-white/20 rounded-lg px-3 py-1.5 text-white text-sm focus:border-amber-500 focus:outline-none"
              >
                {[1, 2, 3, 4, 5].map(n => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </div>

            {/* Video toggle */}
            <div className="flex items-center gap-3 px-3 py-2 bg-white/5 rounded-lg border border-white/10">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useVideo}
                  onChange={(e) => setUseVideo(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-500 text-amber-500 focus:ring-amber-500 focus:ring-offset-0 bg-white/10"
                />
                <span className="text-sm text-gray-300 flex items-center gap-1.5">
                  {useVideo ? <Video className="w-4 h-4 text-purple-400" /> : <Image className="w-4 h-4 text-blue-400" />}
                  {useVideo ? 'Video' : 'Image'}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  useVideo 
                    ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' 
                    : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                }`}>
                  {useVideo ? '~$1.00' : '$0.03'}
                </span>
              </label>
            </div>

            {/* Generate button */}
            <Button 
              onClick={() => onGenerate(numPosts, useVideo)} 
              variant="primary" 
              loading={loading}
            >
              <Sparkles className="w-4 h-4" /> 
              Generate {useVideo ? 'Video' : 'Image'}
            </Button>
          </div>
        </div>

        {/* Video info banner */}
        {useVideo && (
          <div className="mt-4 p-3 bg-purple-500/10 border border-purple-500/20 rounded-lg">
            <p className="text-purple-300 text-sm flex items-center gap-2">
              <Video className="w-4 h-4" />
              <span>
                <strong>Video mode:</strong> 8-second cinematic video with Veo 3.1 Fast • 
                Est. cost: <strong>${estimatedCost}</strong>
              </span>
            </p>
          </div>
        )}
      </Card>

      {/* Queue List */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-white">Post Queue ({posts.length})</h3>
      </div>

      {posts.length === 0 ? (
        <Card>
          <div className="text-center py-8">
            <FileText className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">Queue is empty</p>
            <p className="text-gray-500 text-sm mt-1">Generate content to add posts to the queue</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          {posts.map((post, index) => {
            const isVideo = post.media_type === 'video' || post.image_url?.includes('/videos/') || post.image_url?.endsWith('.mp4');
            const mediaUrl = isVideo ? getVideoUrl(post.image_url) : getImageUrl(post.image_url);
            
            return (
              <Card key={post.id || index}>
                <div className="flex gap-4">
                  {/* Media Preview */}
                  {mediaUrl && (
                    <div 
                      className="flex-shrink-0 w-32 h-32 md:w-40 md:h-40 relative group cursor-pointer"
                      onClick={() => handleMediaClick(post)}
                    >
                      {isVideo ? (
                        <>
                          <video 
                            src={mediaUrl}
                            className="w-full h-full object-cover rounded-lg border border-white/10"
                            muted
                            onError={(e) => {
                              e.target.style.display = 'none';
                              e.target.nextSibling.style.display = 'flex';
                            }}
                          />
                          <div 
                            className="hidden w-full h-full bg-white/5 rounded-lg border border-white/10 items-center justify-center"
                          >
                            <Video className="w-8 h-8 text-gray-500" />
                          </div>
                          {/* Play icon overlay */}
                          <div className="absolute inset-0 flex items-center justify-center">
                            <div className="w-12 h-12 bg-black/50 rounded-full flex items-center justify-center">
                              <Play className="w-6 h-6 text-white ml-1" />
                            </div>
                          </div>
                        </>
                      ) : (
                        <>
                          <img 
                            src={mediaUrl} 
                            alt="Post image" 
                            className="w-full h-full object-cover rounded-lg border border-white/10"
                            onError={(e) => {
                              e.target.style.display = 'none';
                              e.target.nextSibling.style.display = 'flex';
                            }}
                          />
                          <div 
                            className="hidden w-full h-full bg-white/5 rounded-lg border border-white/10 items-center justify-center"
                          >
                            <Image className="w-8 h-8 text-gray-500" />
                          </div>
                        </>
                      )}
                      {/* Zoom overlay */}
                      <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center">
                        <ZoomIn className="w-8 h-8 text-white" />
                      </div>
                    </div>
                  )}

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <StatusBadge active={post.status === 'pending'} label={post.status} />
                      {post.image_url && (
                        <span className={`text-sm flex items-center gap-1 ${isVideo ? 'text-purple-400' : 'text-blue-400'}`}>
                          {isVideo ? <Video className="w-4 h-4" /> : <Image className="w-4 h-4" />}
                          {isVideo ? 'Has video' : 'Has image'}
                        </span>
                      )}
                      {(post.validation_score || post.average_score) && (
                        <span className="text-amber-400 text-sm">
                          Score: {(post.validation_score || post.average_score).toFixed(1)}/10
                        </span>
                      )}
                    </div>
                    <p className="text-gray-300 leading-relaxed mb-2">{post.content}</p>
                    {post.hashtags?.length > 0 && (
                      <p className="text-amber-400 text-sm">
                        {post.hashtags.map(h => h.startsWith('#') ? h : `#${h}`).join(' ')}
                      </p>
                    )}
                    {post.cultural_reference && (
                      <p className="text-purple-400 text-xs mt-2">
                        📺 {renderCulturalReference(post.cultural_reference)}
                      </p>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex-shrink-0">
                    <Button onClick={() => onRemove(post.id)} variant="danger">
                      Remove
                    </Button>
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
    <div className="space-y-6">
      {/* Media Modal */}
      {selectedMedia && (
        <MediaModal 
          mediaUrl={selectedMedia}
          mediaType={selectedMediaType}
          onClose={() => setSelectedMedia(null)} 
        />
      )}

      <h3 className="text-lg font-semibold text-white">Published Posts</h3>

      {posts.length === 0 ? (
        <Card>
          <div className="text-center py-8">
            <History className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No posts published yet</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          {posts.map((post, index) => {
            const isVideo = post.media_type === 'video' || post.image_url?.includes('/videos/') || post.image_url?.endsWith('.mp4');
            const mediaUrl = isVideo ? getVideoUrl(post.image_url) : getImageUrl(post.image_url);
            
            return (
              <Card key={post.id || index}>
                <div className="flex gap-4">
                  {/* Media Preview */}
                  {mediaUrl && (
                    <div 
                      className="flex-shrink-0 w-24 h-24 relative group cursor-pointer"
                      onClick={() => handleMediaClick(post)}
                    >
                      {isVideo ? (
                        <>
                          <video 
                            src={mediaUrl}
                            className="w-full h-full object-cover rounded-lg border border-white/10"
                            muted
                            onError={(e) => { e.target.style.display = 'none'; }}
                          />
                          <div className="absolute inset-0 flex items-center justify-center">
                            <div className="w-8 h-8 bg-black/50 rounded-full flex items-center justify-center">
                              <Play className="w-4 h-4 text-white ml-0.5" />
                            </div>
                          </div>
                        </>
                      ) : (
                        <img 
                          src={mediaUrl} 
                          alt="Post image" 
                          className="w-full h-full object-cover rounded-lg border border-white/10"
                          onError={(e) => { e.target.style.display = 'none'; }}
                        />
                      )}
                      <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center">
                        <ZoomIn className="w-6 h-6 text-white" />
                      </div>
                    </div>
                  )}

                  {/* Content */}
                  <div className="flex-1">
                    <div className="flex items-start gap-3">
                      {post.status === 'success' ? (
                        <CheckCircle className="w-5 h-5 text-green-400 mt-1 flex-shrink-0" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-red-400 mt-1 flex-shrink-0" />
                      )}
                      <div className="flex-1">
                        <div className="flex flex-wrap items-center gap-3 mb-2">
                          <span className="text-gray-400 text-sm">
                            {new Date(post.published_at).toLocaleString()}
                          </span>
                          {post.linkedin_post_id && (
                            <span className="text-blue-400 text-sm">
                              ID: {post.linkedin_post_id}
                            </span>
                          )}
                          {isVideo && (
                            <span className="text-purple-400 text-sm flex items-center gap-1">
                              <Video className="w-3 h-3" /> Video
                            </span>
                          )}
                        </div>
                        <p className="text-gray-300">{post.content}</p>
                        {post.error_message && (
                          <p className="text-red-400 text-sm mt-2">{post.error_message}</p>
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

  const handlePostNow = async () => {
    setLoading(true);
    try {
      await api.post('/api/automation/post-now');
      showMessage('✅ Post triggered! Check history for results.');
      setTimeout(refresh, 2000);
    } catch (err) {
      showMessage(`❌ Failed: ${err.message}`);
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

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'schedule', label: 'Schedule', icon: Calendar },
    { id: 'queue', label: 'Queue', icon: FileText },
    { id: 'history', label: 'History', icon: History },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <header className="border-b border-white/10 bg-black/20 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-amber-400 to-amber-600 rounded-lg flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-black" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Jesse A. Eisenbalm</h1>
                <p className="text-gray-400 text-sm">Automation Dashboard</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <StatusBadge 
                active={status?.scheduler?.running} 
                label={status?.scheduler?.running ? 'Running' : 'Stopped'} 
              />
            </div>
          </div>
        </div>
      </header>

      {/* Message Toast */}
      {message && (
        <div className="fixed top-20 right-6 z-50 bg-gray-800 border border-white/20 rounded-lg px-4 py-3 shadow-xl">
          <p className="text-white">{message}</p>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="bg-red-500/10 border-b border-red-500/30 px-6 py-3">
          <div className="max-w-7xl mx-auto flex items-center gap-3 text-red-400">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
            <button onClick={refresh} className="ml-auto text-sm underline">Retry</button>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6">
          <nav className="flex gap-1">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-3 flex items-center gap-2 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-amber-500 text-amber-400'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
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
            loading={loading}
          />
        )}
        {activeTab === 'history' && (
          <HistoryTab history={history} />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 py-6 mt-auto">
        <div className="max-w-7xl mx-auto px-6 text-center text-gray-500 text-sm">
          <p>Jesse A. Eisenbalm Automation v2.0 • "The only business lip balm that keeps you human in an AI world"</p>
        </div>
      </footer>
    </div>
  );
}