import { useState, useEffect, useCallback } from 'react';
import {
  Brain, RefreshCw, Calendar, TrendingUp, AlertTriangle,
  ChevronDown, ChevronUp, Lightbulb, BarChart3, Play, CheckCircle,
  Clock, Target
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001';

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
  }
};

// ============== Sub-components ==============

function Card({ children, className = '' }) {
  return (
    <div className={`bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4 sm:p-5 ${className}`}>
      {children}
    </div>
  );
}

function SectionTitle({ icon: Icon, title, action }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center gap-2 text-white">
        <Icon className="w-5 h-5 text-amber-400" />
        <h3 className="font-semibold text-sm sm:text-base">{title}</h3>
      </div>
      {action}
    </div>
  );
}

function ThemeBar({ theme, count, maxCount, engagement }) {
  const pct = maxCount > 0 ? (count / maxCount) * 100 : 0;
  const themeColors = {
    ai_slop: 'bg-purple-500',
    ai_safety: 'bg-red-500',
    ai_economy: 'bg-blue-500',
    rituals: 'bg-green-500',
    meditations: 'bg-amber-500',
    unclassified: 'bg-gray-500',
  };
  const color = themeColors[theme] || 'bg-gray-500';
  const label = theme.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-gray-400 w-28 truncate" title={label}>{label}</span>
      <div className="flex-1 bg-white/5 rounded-full h-5 overflow-hidden">
        <div
          className={`${color} h-full rounded-full transition-all duration-500 flex items-center justify-end pr-2`}
          style={{ width: `${Math.max(pct, 8)}%` }}
        >
          <span className="text-[10px] text-white font-medium">{count}</span>
        </div>
      </div>
      {engagement !== undefined && (
        <span className="text-xs text-gray-500 w-12 text-right">{engagement.toFixed(0)} eng</span>
      )}
    </div>
  );
}

function InsightCard({ insight }) {
  const [expanded, setExpanded] = useState(false);
  const typeColors = {
    format_learning: 'text-blue-400 bg-blue-500/10',
    theme_performance: 'text-purple-400 bg-purple-500/10',
    timing: 'text-green-400 bg-green-500/10',
    voice: 'text-amber-400 bg-amber-500/10',
    engagement_pattern: 'text-cyan-400 bg-cyan-500/10',
    portfolio_qc: 'text-pink-400 bg-pink-500/10',
    drift_alert: 'text-red-400 bg-red-500/10',
    weekly_avoid: 'text-orange-400 bg-orange-500/10',
    weekly_double_down: 'text-emerald-400 bg-emerald-500/10',
  };

  const type = insight.insight_type || 'general';
  const colorClass = typeColors[type] || 'text-gray-400 bg-gray-500/10';

  // Try to parse JSON observation (portfolio_qc stores JSON)
  let observation = insight.observation || '';
  let parsedQC = null;
  if (type === 'portfolio_qc') {
    try {
      parsedQC = JSON.parse(observation);
      observation = parsedQC.summary || observation;
    } catch { /* keep as string */ }
  }

  const confidence = insight.confidence || 0;
  const evidenceCount = insight.evidence_count || 0;

  return (
    <div
      className="bg-white/5 rounded-lg p-3 cursor-pointer hover:bg-white/10 transition-colors"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start gap-2">
        <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${colorClass}`}>
          {type.replace(/_/g, ' ')}
        </span>
        <p className="text-gray-300 text-sm flex-1 line-clamp-2">{observation}</p>
        {expanded ? <ChevronUp className="w-4 h-4 text-gray-500 flex-shrink-0" /> : <ChevronDown className="w-4 h-4 text-gray-500 flex-shrink-0" />}
      </div>
      <div className="flex items-center gap-3 mt-2">
        <div className="flex items-center gap-1">
          <div className="w-16 bg-white/10 rounded-full h-1.5">
            <div className="bg-amber-500 h-full rounded-full" style={{ width: `${confidence * 100}%` }} />
          </div>
          <span className="text-[10px] text-gray-500">{(confidence * 100).toFixed(0)}%</span>
        </div>
        <span className="text-[10px] text-gray-500">{evidenceCount} evidence</span>
      </div>
      {expanded && parsedQC && (
        <div className="mt-3 pt-3 border-t border-white/10 grid grid-cols-2 gap-2 text-xs">
          <div><span className="text-gray-500">Voice:</span> <span className="text-white">{parsedQC.voice_consistency}/10</span></div>
          <div><span className="text-gray-500">Positioning:</span> <span className="text-white">{parsedQC.positioning_adherence}/10</span></div>
          <div><span className="text-gray-500">Diversity:</span> <span className="text-white">{parsedQC.diversity_score}/10</span></div>
          <div><span className="text-gray-500">Drift:</span> <span className={parsedQC.drift_detected ? 'text-red-400' : 'text-green-400'}>{parsedQC.tone_drift || 'none'}</span></div>
        </div>
      )}
    </div>
  );
}

function CalendarDay({ entry }) {
  const statusColors = {
    planned: 'border-amber-500/30 bg-amber-500/5',
    generating: 'border-blue-500/30 bg-blue-500/5',
    posted: 'border-green-500/30 bg-green-500/5',
  };
  const statusIcons = {
    planned: Clock,
    generating: RefreshCw,
    posted: CheckCircle,
  };
  const StatusIcon = statusIcons[entry.status] || Clock;
  const borderColor = statusColors[entry.status] || 'border-white/10';

  const dayName = new Date(entry.scheduled_for + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short' });
  const dayNum = new Date(entry.scheduled_for + 'T12:00:00').getDate();
  const themeLabel = (entry.theme || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

  return (
    <div className={`border rounded-lg p-3 ${borderColor}`}>
      <div className="flex items-center justify-between mb-2">
        <div>
          <span className="text-white font-medium text-sm">{dayName}</span>
          <span className="text-gray-500 text-xs ml-1">{dayNum}</span>
        </div>
        <StatusIcon className="w-3.5 h-3.5 text-gray-400" />
      </div>
      <span className="text-amber-400 text-xs font-medium">{themeLabel}</span>
      {entry.format && <span className="text-gray-500 text-[10px] ml-2">{entry.format}</span>}
      {entry.angle_seed && (
        <p className="text-gray-400 text-xs mt-1.5 line-clamp-2">{entry.angle_seed}</p>
      )}
    </div>
  );
}

function PerformanceRow({ post }) {
  const eng = post.engagement_score || 0;
  const maxEng = 50; // reasonable max for bar width
  const pct = Math.min((eng / maxEng) * 100, 100);
  const themeLabel = (post.theme || '?').replace(/_/g, ' ');
  const date = (post.created_at || '').slice(0, 10);

  return (
    <div className="flex items-center gap-3 py-2 border-b border-white/5 last:border-0">
      <span className="text-[10px] text-gray-500 w-16">{date}</span>
      <span className="text-xs text-gray-400 w-20 truncate">{themeLabel}</span>
      <div className="flex-1 bg-white/5 rounded-full h-3 overflow-hidden">
        <div
          className="bg-gradient-to-r from-amber-500 to-amber-400 h-full rounded-full transition-all"
          style={{ width: `${Math.max(pct, 4)}%` }}
        />
      </div>
      <div className="flex gap-2 text-[10px] text-gray-500 w-32 justify-end">
        <span>{post.reactions || 0}r</span>
        <span>{post.comments || 0}c</span>
        <span>{post.shares || 0}s</span>
        <span>{post.impressions || 0}i</span>
      </div>
    </div>
  );
}

// ============== Main Component ==============

export default function StrategyTab() {
  const [calendar, setCalendar] = useState([]);
  const [insights, setInsights] = useState([]);
  const [performance, setPerformance] = useState([]);
  const [themeDistribution, setThemeDistribution] = useState({});
  const [adaptiveWeights, setAdaptiveWeights] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  const [message, setMessage] = useState('');

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [calRes, insRes, perfRes, weightsRes] = await Promise.all([
        api.get('/api/automation/calendar'),
        api.get('/api/automation/strategy-insights?top=20'),
        api.get('/api/automation/performance?days=14'),
        api.get('/api/automation/adaptive-weights?days=30').catch(() => ({ success: false })),
      ]);
      setCalendar(calRes.entries || []);
      setInsights(insRes.insights || []);
      setPerformance(perfRes.posts || []);

      // Compute theme distribution from performance data
      const dist = {};
      const engByTheme = {};
      for (const p of (perfRes.posts || [])) {
        const t = p.theme || 'unclassified';
        dist[t] = (dist[t] || 0) + 1;
        engByTheme[t] = (engByTheme[t] || 0) + (p.engagement_score || 0);
      }
      // Average engagement per theme
      for (const t of Object.keys(engByTheme)) {
        engByTheme[t] = dist[t] > 0 ? engByTheme[t] / dist[t] : 0;
      }
      setThemeDistribution({ counts: dist, avgEngagement: engByTheme });
      if (weightsRes.success) setAdaptiveWeights(weightsRes);
    } catch (e) {
      console.error('Strategy fetch error:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const runAction = async (endpoint, label) => {
    setActionLoading(label);
    setMessage('');
    try {
      await api.post(endpoint);
      setMessage(`${label} started — running in background`);
      // Refresh after a short delay
      setTimeout(fetchAll, 3000);
    } catch (e) {
      setMessage(`Failed: ${e.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const maxThemeCount = Math.max(...Object.values(themeDistribution.counts || {}), 1);

  return (
    <div className="space-y-6">
      {/* Message toast */}
      {message && (
        <div className="bg-gray-800/90 border border-white/20 rounded-xl px-4 py-3 text-sm text-white animate-pulse">
          {message}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => runAction('/api/automation/ingest-performance', 'Ingestion')}
          disabled={actionLoading}
          className="flex items-center gap-2 px-3 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-gray-300 transition-colors disabled:opacity-50"
        >
          <TrendingUp className="w-4 h-4" />
          {actionLoading === 'Ingestion' ? 'Running...' : 'Ingest Performance'}
        </button>
        <button
          onClick={() => runAction('/api/automation/run-refinement', 'Refinement')}
          disabled={actionLoading}
          className="flex items-center gap-2 px-3 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-gray-300 transition-colors disabled:opacity-50"
        >
          <Lightbulb className="w-4 h-4" />
          {actionLoading === 'Refinement' ? 'Running...' : 'Run Refinement'}
        </button>
        <button
          onClick={() => runAction('/api/automation/run-strategist', 'Strategist')}
          disabled={actionLoading}
          className="flex items-center gap-2 px-3 py-2 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 rounded-lg text-sm text-amber-400 transition-colors disabled:opacity-50"
        >
          <Brain className="w-4 h-4" />
          {actionLoading === 'Strategist' ? 'Planning...' : 'Run Strategist'}
        </button>
        <button
          onClick={() => runAction('/api/automation/run-portfolio-qc', 'QC')}
          disabled={actionLoading}
          className="flex items-center gap-2 px-3 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-gray-300 transition-colors disabled:opacity-50"
        >
          <Target className="w-4 h-4" />
          {actionLoading === 'QC' ? 'Running...' : 'Run QC'}
        </button>
        <button
          onClick={fetchAll}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-gray-300 transition-colors disabled:opacity-50 ml-auto"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Editorial Calendar */}
      <Card>
        <SectionTitle icon={Calendar} title="Editorial Calendar" />
        {calendar.length === 0 ? (
          <p className="text-gray-500 text-sm">No calendar entries yet. Run the strategist to plan the week.</p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
            {calendar.map(entry => (
              <CalendarDay key={entry.id} entry={entry} />
            ))}
          </div>
        )}
      </Card>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Theme Distribution */}
        <Card>
          <SectionTitle icon={BarChart3} title="Theme Distribution (14d)" />
          {Object.keys(themeDistribution.counts || {}).length === 0 ? (
            <p className="text-gray-500 text-sm">No theme data available yet.</p>
          ) : (
            <div className="space-y-2">
              {Object.entries(themeDistribution.counts || {})
                .sort((a, b) => b[1] - a[1])
                .map(([theme, count]) => (
                  <ThemeBar
                    key={theme}
                    theme={theme}
                    count={count}
                    maxCount={maxThemeCount}
                    engagement={(themeDistribution.avgEngagement || {})[theme]}
                  />
                ))}
            </div>
          )}
        </Card>

        {/* Performance */}
        <Card>
          <SectionTitle icon={TrendingUp} title="Post Performance (14d)" />
          {performance.length === 0 ? (
            <p className="text-gray-500 text-sm">No performance data yet. Run ingestion first.</p>
          ) : (
            <div className="max-h-64 overflow-y-auto">
              {performance.map((post, i) => (
                <PerformanceRow key={post.post_id || i} post={post} />
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Adaptive Weights & Format Testing */}
      {adaptiveWeights && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Adaptive Theme Weights */}
          <Card>
            <SectionTitle icon={Target} title="Adaptive Theme Weights (30d)" />
            {Object.keys(adaptiveWeights.adaptive_weights || {}).length === 0 ? (
              <p className="text-gray-500 text-sm">Not enough data to compute weights.</p>
            ) : (
              <div className="space-y-2">
                {Object.entries(adaptiveWeights.adaptive_weights)
                  .sort((a, b) => b[1] - a[1])
                  .map(([theme, weight]) => {
                    const label = theme.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                    const pct = (weight * 100).toFixed(0);
                    return (
                      <div key={theme} className="flex items-center gap-3">
                        <span className="text-xs text-gray-400 w-28 truncate">{label}</span>
                        <div className="flex-1 bg-white/5 rounded-full h-4 overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-amber-600 to-amber-400 h-full rounded-full transition-all"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-300 w-10 text-right">{pct}%</span>
                      </div>
                    );
                  })}
              </div>
            )}
          </Card>

          {/* Format A/B Testing */}
          <Card>
            <SectionTitle icon={BarChart3} title="Format Performance & A/B Testing" />
            {Object.keys(adaptiveWeights.format_performance || {}).length === 0 && (adaptiveWeights.underexplored_formats || []).length === 0 ? (
              <p className="text-gray-500 text-sm">Not enough format data yet.</p>
            ) : (
              <>
                {Object.entries(adaptiveWeights.format_performance || {})
                  .sort((a, b) => (b[1].avg_engagement || 0) - (a[1].avg_engagement || 0))
                  .map(([fmt, data]) => (
                    <div key={fmt} className="flex items-center gap-3 py-1.5">
                      <span className="text-xs text-gray-400 w-24 truncate">{fmt.replace(/_/g, ' ')}</span>
                      <div className="flex-1 bg-white/5 rounded-full h-3 overflow-hidden">
                        <div
                          className="bg-blue-500 h-full rounded-full"
                          style={{ width: `${Math.min(((data.avg_engagement || 0) / 50) * 100, 100)}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-gray-500 w-16 text-right">{data.count} posts</span>
                      <span className="text-[10px] text-gray-400 w-14 text-right">{(data.avg_engagement || 0).toFixed(0)} eng</span>
                    </div>
                  ))}
                {(adaptiveWeights.underexplored_formats || []).length > 0 && (
                  <div className="mt-3 pt-3 border-t border-white/10">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                      <span className="text-xs text-amber-400 font-medium">Underexplored formats</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {adaptiveWeights.underexplored_formats.map(fmt => (
                        <span key={fmt} className="text-[10px] px-2 py-1 bg-amber-500/10 text-amber-300 rounded-md">
                          {fmt.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </Card>
        </div>
      )}

      {/* Strategy Insights */}
      <Card>
        <SectionTitle icon={Lightbulb} title={`Strategy Insights (${insights.length})`} />
        {insights.length === 0 ? (
          <p className="text-gray-500 text-sm">No insights yet. Run the refinement agent to generate learnings.</p>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {insights.map((ins, i) => (
              <InsightCard key={ins.id || i} insight={ins} />
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
