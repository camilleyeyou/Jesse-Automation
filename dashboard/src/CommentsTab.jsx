/**
 * CommentsTab Component for Jesse A. Eisenbalm Dashboard
 * 
 * LinkedIn Comment Engagement System - Mobile Responsive
 * 
 * Features:
 * - Generate comment options for LinkedIn posts
 * - Review and approve/reject comments
 * - Post comments to LinkedIn
 * - Track engagement metrics
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  MessageCircle, ExternalLink, ThumbsUp, MessageSquare, 
  Copy, Check, Sparkles, RefreshCw, X, Send, AlertCircle,
  CheckCircle, XCircle, Clock, Trash2
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001';

// API helper
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

// UI Components
function Card({ children, className = '' }) {
  return (
    <div className={`bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4 md:p-6 ${className}`}>
      {children}
    </div>
  );
}

function Button({ children, onClick, variant = 'primary', disabled = false, loading = false, size = 'md' }) {
  const variants = {
    primary: 'bg-amber-500 hover:bg-amber-400 text-black',
    secondary: 'bg-white/10 hover:bg-white/20 text-white border border-white/20',
    danger: 'bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30',
    success: 'bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/30'
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg'
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`${sizes[size]} rounded-lg font-medium transition-all flex items-center gap-2 
        ${variants[variant]} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      {loading && <RefreshCw className="w-4 h-4 animate-spin" />}
      {children}
    </button>
  );
}

function StatusBadge({ status }) {
  const statusConfig = {
    pending: { color: 'amber', label: 'Pending' },
    approved: { color: 'blue', label: 'Approved' },
    posted: { color: 'green', label: 'Posted' },
    rejected: { color: 'red', label: 'Rejected' },
    failed: { color: 'red', label: 'Failed' }
  };

  const config = statusConfig[status] || { color: 'gray', label: status };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium 
      bg-${config.color}-500/20 text-${config.color}-400 border border-${config.color}-500/30`}>
      {config.label}
    </span>
  );
}

// Style badge
function StyleBadge({ style }) {
  const styleColors = {
    knowing_nod: 'blue',
    absurdist_tangent: 'purple',
    human_moment: 'green',
    witty_insight: 'amber',
    warm_encouragement: 'pink'
  };

  const color = styleColors[style] || 'gray';
  const label = style?.replace(/_/g, ' ');

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium capitalize
      bg-${color}-500/20 text-${color}-300 border border-${color}-500/30`}>
      {label}
    </span>
  );
}

// Comment Generator Form
function CommentGeneratorForm({ onGenerate, onCancel, loading }) {
  const [postUrl, setPostUrl] = useState('');
  const [postContent, setPostContent] = useState('');
  const [authorName, setAuthorName] = useState('');

  const handleSubmit = () => {
    if (!postUrl.trim() || !postContent.trim()) return;
    onGenerate({ postUrl, postContent, authorName });
  };

  return (
    <Card className="mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-amber-400" />
          Generate Comment
        </h3>
        <button onClick={onCancel} className="text-gray-400 hover:text-white">
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">LinkedIn Post URL *</label>
          <input
            type="url"
            value={postUrl}
            onChange={(e) => setPostUrl(e.target.value)}
            placeholder="https://www.linkedin.com/feed/update/..."
            className="w-full bg-white/5 border border-white/20 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:border-amber-500 focus:outline-none"
          />
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-1">Post Content *</label>
          <textarea
            value={postContent}
            onChange={(e) => setPostContent(e.target.value)}
            placeholder="Paste the LinkedIn post text here..."
            rows={4}
            className="w-full bg-white/5 border border-white/20 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:border-amber-500 focus:outline-none resize-none"
          />
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-1">Author Name (optional)</label>
          <input
            type="text"
            value={authorName}
            onChange={(e) => setAuthorName(e.target.value)}
            placeholder="Post author's name"
            className="w-full bg-white/5 border border-white/20 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:border-amber-500 focus:outline-none"
          />
        </div>

        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          <Button 
            onClick={handleSubmit} 
            variant="primary" 
            loading={loading}
            disabled={!postUrl.trim() || !postContent.trim()}
          >
            <Sparkles className="w-4 h-4" /> Generate 3 Options
          </Button>
          <Button onClick={onCancel} variant="secondary">
            Cancel
          </Button>
        </div>
      </div>
    </Card>
  );
}

// Comment Card
function CommentCard({ comment, onApprove, onReject, onPost, onDelete, loading }) {
  const [expanded, setExpanded] = useState(false);
  const [selectedOptionId, setSelectedOptionId] = useState(comment.selected_option_id);
  const [editedText, setEditedText] = useState(comment.final_comment || '');
  const [copiedId, setCopiedId] = useState(null);

  const options = comment.comment_options || [];
  const sourcePost = comment.source_post || {};

  const copyToClipboard = async (text, id) => {
    await navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSelectOption = (optionId, content) => {
    setSelectedOptionId(optionId);
    setEditedText(content);
  };

  return (
    <Card className="mb-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-3">
          <StatusBadge status={comment.status} />
          <span className="text-gray-400 text-sm">
            {new Date(comment.created_at).toLocaleDateString()}
          </span>
        </div>
        
        {/* Engagement stats (if posted) */}
        {comment.status === 'posted' && (
          <div className="flex items-center gap-4 text-sm">
            <span className="text-gray-400 flex items-center gap-1">
              <ThumbsUp className="w-4 h-4" /> {comment.engagement?.likes || 0}
            </span>
            <span className="text-gray-400 flex items-center gap-1">
              <MessageSquare className="w-4 h-4" /> {comment.engagement?.replies || 0}
            </span>
          </div>
        )}
      </div>

      {/* Source Post Info */}
      <div className="mb-4 p-3 bg-white/5 rounded-lg border border-white/10">
        <div className="flex items-start justify-between gap-2 mb-2">
          <p className="text-sm text-gray-400">
            Commenting on: <span className="text-white">{sourcePost.author_name || 'Unknown'}</span>
          </p>
          <a 
            href={sourcePost.url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-amber-400 hover:text-amber-300 flex-shrink-0"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
        <p className="text-gray-300 text-sm line-clamp-2">{sourcePost.content}</p>
        <div className="flex flex-wrap gap-2 mt-2">
          <span className="text-xs text-gray-500">Topic: {sourcePost.topic}</span>
          <span className="text-xs text-gray-500">Tone: {sourcePost.tone}</span>
        </div>
      </div>

      {/* Comment Options (expandable) */}
      {comment.status === 'pending' && (
        <>
          <button 
            onClick={() => setExpanded(!expanded)}
            className="text-amber-400 text-sm hover:text-amber-300 mb-3 flex items-center gap-1"
          >
            {expanded ? 'Hide options' : `View ${options.length} options`}
          </button>

          {expanded && (
            <div className="space-y-3 mb-4">
              {options.map((option, idx) => (
                <div 
                  key={option.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    selectedOptionId === option.id
                      ? 'border-amber-500 bg-amber-500/10'
                      : 'border-white/10 bg-white/5 hover:border-white/30'
                  }`}
                  onClick={() => handleSelectOption(option.id, option.content)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <StyleBadge style={option.style} />
                      <span className="text-amber-400 text-sm">
                        Score: {option.overall_score?.toFixed(1)}
                      </span>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        copyToClipboard(option.content, option.id);
                      }}
                      className="text-gray-400 hover:text-white p-1"
                    >
                      {copiedId === option.id ? (
                        <Check className="w-4 h-4 text-green-400" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                  <p className="text-white text-sm">{option.content}</p>
                  {option.reasoning && (
                    <p className="text-gray-500 text-xs mt-2 italic">{option.reasoning}</p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Edit area */}
          <div className="mb-4">
            <label className="block text-sm text-gray-400 mb-1">Selected/Edited Comment:</label>
            <textarea
              value={editedText}
              onChange={(e) => setEditedText(e.target.value)}
              rows={3}
              className="w-full bg-white/5 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:border-amber-500 focus:outline-none resize-none"
            />
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap gap-2">
            <Button 
              onClick={() => onApprove(comment.id, selectedOptionId, editedText)}
              variant="success"
              size="sm"
              loading={loading}
            >
              <CheckCircle className="w-4 h-4" /> Approve
            </Button>
            <Button 
              onClick={() => onReject(comment.id)}
              variant="danger"
              size="sm"
              loading={loading}
            >
              <XCircle className="w-4 h-4" /> Reject
            </Button>
            <Button 
              onClick={() => onDelete(comment.id)}
              variant="secondary"
              size="sm"
              loading={loading}
            >
              <Trash2 className="w-4 h-4" /> Delete
            </Button>
          </div>
        </>
      )}

      {/* Approved state */}
      {comment.status === 'approved' && (
        <>
          <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
            <p className="text-blue-300 text-sm">{comment.final_comment}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button 
              onClick={() => onPost(comment.id)}
              variant="primary"
              size="sm"
              loading={loading}
            >
              <Send className="w-4 h-4" /> Post to LinkedIn
            </Button>
            <Button 
              onClick={() => onDelete(comment.id)}
              variant="secondary"
              size="sm"
              loading={loading}
            >
              <Trash2 className="w-4 h-4" /> Delete
            </Button>
          </div>
        </>
      )}

      {/* Posted state */}
      {comment.status === 'posted' && (
        <div className="p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
          <p className="text-green-300 text-sm">{comment.final_comment}</p>
          <p className="text-green-400/70 text-xs mt-2">
            Posted {comment.posted_at ? new Date(comment.posted_at).toLocaleString() : 'recently'}
          </p>
        </div>
      )}

      {/* Rejected state */}
      {comment.status === 'rejected' && (
        <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
          <p className="text-red-300 text-sm line-through">{comment.final_comment}</p>
          <p className="text-red-400/70 text-xs mt-2">Rejected</p>
        </div>
      )}
    </Card>
  );
}

// Main CommentsTab Component
export default function CommentsTab() {
  const [comments, setComments] = useState([]);
  const [history, setHistory] = useState([]);
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(false);
  const [showGenerator, setShowGenerator] = useState(false);
  const [activeView, setActiveView] = useState('queue'); // 'queue' | 'history'
  const [message, setMessage] = useState(null);

  // Fetch comments queue
  const fetchComments = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.get('/api/comments/queue?limit=50');
      setComments(data.comments || []);
      setSummary(data.summary || {});
    } catch (err) {
      console.error('Failed to fetch comments:', err);
    }
    setLoading(false);
  }, []);

  // Fetch history
  const fetchHistory = useCallback(async () => {
    try {
      const data = await api.get('/api/comments/history?limit=30&include_rejected=true');
      setHistory(data.comments || []);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  }, []);

  useEffect(() => {
    fetchComments();
    fetchHistory();
  }, [fetchComments, fetchHistory]);

  const showMessage = (msg) => {
    setMessage(msg);
    setTimeout(() => setMessage(null), 3000);
  };

  // Generate comments
  const handleGenerate = async ({ postUrl, postContent, authorName }) => {
    setLoading(true);
    try {
      const result = await api.post('/api/comments/generate', {
        post_url: postUrl,
        post_content: postContent,
        author_name: authorName || 'Unknown',
        num_options: 3
      });
      showMessage(`✅ Generated ${result.comment?.comment_options?.length || 3} comment options`);
      setShowGenerator(false);
      await fetchComments();
    } catch (err) {
      showMessage(`❌ Failed: ${err.message}`);
    }
    setLoading(false);
  };

  // Approve comment
  const handleApprove = async (commentId, optionId, editedText) => {
    setLoading(true);
    try {
      // First select the option
      if (optionId) {
        await api.patch(`/api/comments/${commentId}/select?option_id=${optionId}`, {});
      }
      // Then approve
      await api.patch(`/api/comments/${commentId}/approve`, {
        edited_text: editedText,
        approved_by: 'admin',
        post_immediately: false
      });
      showMessage('✅ Comment approved');
      await fetchComments();
    } catch (err) {
      showMessage(`❌ Failed: ${err.message}`);
    }
    setLoading(false);
  };

  // Reject comment
  const handleReject = async (commentId) => {
    setLoading(true);
    try {
      await api.patch(`/api/comments/${commentId}/reject`, {});
      showMessage('✅ Comment rejected');
      await fetchComments();
      await fetchHistory();
    } catch (err) {
      showMessage(`❌ Failed: ${err.message}`);
    }
    setLoading(false);
  };

  // Post comment
  const handlePost = async (commentId) => {
    setLoading(true);
    try {
      await api.post(`/api/comments/${commentId}/post`);
      showMessage('✅ Comment posted to LinkedIn!');
      await fetchComments();
      await fetchHistory();
    } catch (err) {
      showMessage(`❌ Failed: ${err.message}`);
    }
    setLoading(false);
  };

  // Delete comment
  const handleDelete = async (commentId) => {
    if (!confirm('Delete this comment?')) return;
    setLoading(true);
    try {
      await api.delete(`/api/comments/${commentId}`);
      showMessage('✅ Comment deleted');
      await fetchComments();
      await fetchHistory();
    } catch (err) {
      showMessage(`❌ Failed: ${err.message}`);
    }
    setLoading(false);
  };

  const displayComments = activeView === 'queue' ? comments : history;

  return (
    <div className="space-y-6">
      {/* Message Toast */}
      {message && (
        <div className="fixed top-20 right-4 md:right-6 z-50 bg-gray-800 border border-white/20 rounded-lg px-4 py-3 shadow-xl max-w-sm">
          <p className="text-white text-sm">{message}</p>
        </div>
      )}

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 md:gap-4">
        <Card className="text-center">
          <p className="text-2xl md:text-3xl font-bold text-white">{summary.pending || 0}</p>
          <p className="text-gray-400 text-xs md:text-sm">Pending</p>
        </Card>
        <Card className="text-center">
          <p className="text-2xl md:text-3xl font-bold text-white">{summary.approved || 0}</p>
          <p className="text-gray-400 text-xs md:text-sm">Approved</p>
        </Card>
        <Card className="text-center">
          <p className="text-2xl md:text-3xl font-bold text-white">{summary.posted || 0}</p>
          <p className="text-gray-400 text-xs md:text-sm">Posted</p>
        </Card>
        <Card className="text-center">
          <p className="text-2xl md:text-3xl font-bold text-amber-400">{summary.total_likes || 0}</p>
          <p className="text-gray-400 text-xs md:text-sm">Total Likes</p>
        </Card>
        <Card className="text-center col-span-2 md:col-span-1">
          <p className="text-2xl md:text-3xl font-bold text-amber-400">{summary.total_replies || 0}</p>
          <p className="text-gray-400 text-xs md:text-sm">Replies</p>
        </Card>
      </div>

      {/* Actions */}
      <Card>
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <MessageCircle className="w-5 h-5 text-amber-400" />
            Comment Engagement
          </h3>
          <div className="flex flex-wrap gap-2 w-full sm:w-auto">
            <Button 
              onClick={() => setShowGenerator(true)} 
              variant="primary"
              disabled={showGenerator}
            >
              <Sparkles className="w-4 h-4" /> New Comment
            </Button>
            <Button 
              onClick={() => { fetchComments(); fetchHistory(); }} 
              variant="secondary" 
              loading={loading}
            >
              <RefreshCw className="w-4 h-4" /> Refresh
            </Button>
          </div>
        </div>
      </Card>

      {/* Generator Form */}
      {showGenerator && (
        <CommentGeneratorForm 
          onGenerate={handleGenerate}
          onCancel={() => setShowGenerator(false)}
          loading={loading}
        />
      )}

      {/* View Toggle */}
      <div className="flex gap-2 border-b border-white/10 pb-2">
        <button
          onClick={() => setActiveView('queue')}
          className={`px-4 py-2 rounded-t-lg transition-colors ${
            activeView === 'queue'
              ? 'bg-white/10 text-amber-400 border-b-2 border-amber-500'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          Queue ({comments.length})
        </button>
        <button
          onClick={() => setActiveView('history')}
          className={`px-4 py-2 rounded-t-lg transition-colors ${
            activeView === 'history'
              ? 'bg-white/10 text-amber-400 border-b-2 border-amber-500'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          History ({history.length})
        </button>
      </div>

      {/* Comments List */}
      {displayComments.length === 0 ? (
        <Card>
          <div className="text-center py-8">
            <MessageCircle className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">
              {activeView === 'queue' 
                ? 'No comments in queue' 
                : 'No comment history yet'}
            </p>
            <p className="text-gray-500 text-sm mt-1">
              {activeView === 'queue' 
                ? 'Generate comments for LinkedIn posts to get started' 
                : 'Approved and posted comments will appear here'}
            </p>
          </div>
        </Card>
      ) : (
        <div>
          {displayComments.map((comment) => (
            <CommentCard
              key={comment.id}
              comment={comment}
              onApprove={handleApprove}
              onReject={handleReject}
              onPost={handlePost}
              onDelete={handleDelete}
              loading={loading}
            />
          ))}
        </div>
      )}
    </div>
  );
}
