import { useState, useEffect } from 'react'
import {
  Rocket,
  CheckCircle2,
  AlertTriangle,
  X,
  Loader2,
  Server,
  GitCommit,
  Layers,
  Sparkles,
} from 'lucide-react'
import {
  fetchRevisions,
  fetchTargets,
  createDeploymentPlan,
  approveDeploymentPlan,
  executeDeploymentPlan,
  Revision,
  Target,
  DeploymentPlan,
} from '../../api/client'

export function DeployModal({
  isOpen,
  onClose,
  revisionId,
  targetId,
}: {
  isOpen: boolean
  onClose: () => void
  revisionId?: string
  targetId?: string
}) {
  const [revisions, setRevisions] = useState<Revision[]>([])
  const [targets, setTargets] = useState<Target[]>([])
  const [selectedRevisionId, setSelectedRevisionId] = useState<string>('')
  const [selectedTargetId, setSelectedTargetId] = useState<string>('')
  const [loadingMetadata, setLoadingMetadata] = useState(false)

  const [step, setStep] = useState<
    'idle' | 'planning' | 'planned' | 'approving' | 'approved' | 'deploying' | 'done'
  >('idle')
  const [plan, setPlan] = useState<DeploymentPlan | null>(null)
  const [executionResult, setExecutionResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isOpen) return

    setLoadingMetadata(true)
    setError(null)
    setStep('idle')
    setPlan(null)
    setExecutionResult(null)

    Promise.all([fetchRevisions(), fetchTargets()])
      .then(([revs, tgts]) => {
        setRevisions(revs)
        setTargets(tgts)

        // Choose initial revision: passed revisionId if found, else latest snapshot (revs[0])
        if (revisionId && revs.some((r) => r.id === revisionId)) {
          setSelectedRevisionId(revisionId)
        } else if (revs.length > 0) {
          setSelectedRevisionId(revs[0].id)
        } else {
          setSelectedRevisionId('')
        }

        // Choose initial target
        if (targetId && tgts.some((t) => t.id === targetId)) {
          setSelectedTargetId(targetId)
        } else if (tgts.length > 0) {
          setSelectedTargetId(tgts[0].id)
        } else if (targetId) {
          setSelectedTargetId(targetId)
        }
      })
      .catch((e: any) => {
        console.error('Error loading deployment options:', e)
        setError('Failed to load project revisions and servers')
      })
      .finally(() => {
        setLoadingMetadata(false)
      })
  }, [isOpen, revisionId, targetId])

  if (!isOpen) return null

  const currentRevision =
    revisions.find((r) => r.id === selectedRevisionId) || (revisions.length > 0 ? revisions[0] : null)
  const isLatestRevision =
    currentRevision && revisions.length > 0 && currentRevision.id === revisions[0].id
  const currentTarget = targets.find((t) => t.id === selectedTargetId)

  const handleCreatePlan = async () => {
    const revToDeploy = selectedRevisionId || currentRevision?.id
    const targetToDeploy = selectedTargetId || targetId
    if (!revToDeploy || !targetToDeploy) {
      setError('Please select both a revision and a target server.')
      return
    }
    setError(null)
    setStep('planning')
    try {
      const generated = await createDeploymentPlan(revToDeploy, targetToDeploy)
      setPlan(generated)
      setStep('planned')
    } catch (e: any) {
      setError(e.message)
      setStep('idle')
    }
  }

  const handleApprovePlan = async () => {
    if (!plan) return
    setError(null)
    setStep('approving')
    try {
      await approveDeploymentPlan(plan.id)
      setStep('approved')
    } catch (e: any) {
      setError(e.message)
      setStep('planned')
    }
  }

  const handleExecute = async () => {
    if (!plan) return
    setError(null)
    setStep('deploying')
    try {
      const result = await executeDeploymentPlan(plan.id)
      setExecutionResult(result)
      setStep('done')
    } catch (e: any) {
      setError(e.message)
      setStep('approved')
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div className="bg-[#18181e] border border-[#2e2e38] rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden flex flex-col">
        {/* Modal Header */}
        <div className="p-5 border-b border-[#2e2e38] flex items-center justify-between bg-[#15151a]">
          <div className="flex items-center space-x-2.5">
            <Rocket className="w-5 h-5 text-emerald-400" />
            <div>
              <h3 className="font-semibold text-gray-100 text-base">Release & Deployment Pipeline</h3>
              <p className="text-[11px] text-gray-400">Canonical Release Engine to Paper 1.21 Server</p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-200">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5">
          {error && (
            <div className="p-3.5 bg-red-950/40 border border-red-800/60 rounded-xl text-xs text-red-300 flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Context Selector: Target Server & Project Revision */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            {/* Target Server Card */}
            <div className="p-3 bg-[#131317] border border-[#272730] rounded-xl space-y-2">
              <div className="flex items-center justify-between text-gray-400 font-medium">
                <span className="flex items-center space-x-1.5">
                  <Server className="w-3.5 h-3.5 text-blue-400" />
                  <span>Target Server</span>
                </span>
                {currentTarget && (
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded-full flex items-center space-x-1 ${
                      currentTarget.status === 'online'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        : 'bg-red-500/10 text-red-400 border border-red-500/30'
                    }`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        currentTarget.status === 'online' ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'
                      }`}
                    />
                    <span className="capitalize">{currentTarget.status}</span>
                  </span>
                )}
              </div>

              {targets.length > 1 && step === 'idle' ? (
                <select
                  value={selectedTargetId}
                  onChange={(e) => setSelectedTargetId(e.target.value)}
                  className="w-full bg-[#1c1c24] border border-[#2e2e3b] text-gray-200 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-blue-500"
                >
                  {targets.map((tgt) => (
                    <option key={tgt.id} value={tgt.id}>
                      {tgt.name || tgt.id} ({tgt.status})
                    </option>
                  ))}
                </select>
              ) : (
                <div className="font-semibold text-gray-200 font-mono truncate">
                  {selectedTargetId || targetId || 'local-paper-server'}
                </div>
              )}
            </div>

            {/* Project Revision Card */}
            <div className="p-3 bg-[#131317] border border-[#272730] rounded-xl space-y-2">
              <div className="flex items-center justify-between text-gray-400 font-medium">
                <span className="flex items-center space-x-1.5">
                  <GitCommit className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Project Revision</span>
                </span>
                {isLatestRevision && (
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                    Latest Snapshot
                  </span>
                )}
              </div>

              {revisions.length > 1 && step === 'idle' ? (
                <select
                  value={selectedRevisionId}
                  onChange={(e) => setSelectedRevisionId(e.target.value)}
                  className="w-full bg-[#1c1c24] border border-[#2e2e3b] text-gray-200 text-xs rounded-lg px-2.5 py-1.5 font-mono focus:outline-none focus:border-emerald-500"
                >
                  {revisions.map((rev, idx) => (
                    <option key={rev.id} value={rev.id}>
                      Rev #{rev.revision_number} ({rev.revision_hash.slice(0, 8)}...) - {rev.items_count} items{rev.blocks_count ? ` • ${rev.blocks_count} props` : ''} {idx === 0 ? '• [LATEST]' : ''}
                    </option>
                  ))}
                </select>
              ) : currentRevision ? (
                <div className="flex items-center space-x-2 font-mono">
                  <span className="font-bold text-emerald-400 text-sm">
                    Rev #{currentRevision.revision_number}
                  </span>
                  <span className="text-gray-400 text-xs">
                    ({currentRevision.revision_hash.slice(0, 8)}...)
                  </span>
                </div>
              ) : (
                <div className="font-medium text-amber-400 font-mono">
                  {revisionId || 'No revisions found'}
                </div>
              )}

              {/* Revision details summary */}
              {currentRevision && (
                <div className="pt-1 border-t border-[#22222a] flex items-center justify-between text-[10px] text-gray-400 font-mono">
                  <span className="flex items-center space-x-1 text-gray-300">
                    <Layers className="w-3 h-3 text-emerald-400" />
                    <span>
                      {currentRevision.items_count} items
                      {currentRevision.blocks_count ? ` • ${currentRevision.blocks_count} props` : ''}
                    </span>
                  </span>
                  <span className="text-gray-500" title={`Database ID: ${currentRevision.id}`}>
                    ID: {currentRevision.id}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Stepper view */}
          {step === 'idle' && (
            <div className="text-center py-6 space-y-4">
              {loadingMetadata ? (
                <div className="flex items-center justify-center space-x-2 text-xs text-gray-400">
                  <Loader2 className="w-4 h-4 text-emerald-400 animate-spin" />
                  <span>Loading latest project revisions...</span>
                </div>
              ) : revisions.length === 0 ? (
                <div className="p-4 bg-amber-950/20 border border-amber-800/40 rounded-xl text-xs text-amber-300">
                  <p className="font-semibold mb-1">No snapshot revisions available</p>
                  <p className="text-amber-400/80">
                    Please use the <strong>Snapshot Revision</strong> button in Items Studio or Block Studio to freeze a canonical revision before deploying.
                  </p>
                </div>
              ) : (
                <>
                  <p className="text-xs text-gray-400">
                    Ready to compile deployment plan for{' '}
                    <strong className="text-emerald-300">
                      Rev #{currentRevision?.revision_number}
                    </strong>{' '}
                    ({currentRevision?.revision_hash.slice(0, 8)}...). Comparing canonical revision against target state.
                  </p>
                  <button
                    onClick={handleCreatePlan}
                    disabled={!selectedRevisionId && !currentRevision}
                    className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-lg shadow-emerald-950/40 transition inline-flex items-center space-x-2"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>
                      Generate Deployment Plan for Rev #{currentRevision?.revision_number}
                    </span>
                  </button>
                </>
              )}
            </div>
          )}

          {step === 'planning' && (
            <div className="text-center py-8 space-y-3">
              <Loader2 className="w-6 h-6 text-emerald-400 animate-spin mx-auto" />
              <div className="text-xs text-gray-400">Analyzing definitions and generating deterministic plan...</div>
            </div>
          )}

          {(step === 'planned' || step === 'approving') && plan && (
            <div className="space-y-4">
              <div className="p-3 bg-[#111114] border border-[#25252e] rounded-xl text-xs">
                <div className="flex justify-between items-center mb-2 pb-1 border-b border-[#25252e]">
                  <span className="text-gray-400">
                    Deploying <strong className="text-emerald-400">Rev #{currentRevision?.revision_number}</strong>:
                  </span>
                  <span className="font-mono text-gray-300 text-[11px]">
                    Plan Hash: {plan.plan_hash.slice(0, 16)}...
                  </span>
                </div>
                <div className="font-semibold text-gray-300 mb-2">Operations ({plan.operations.length}):</div>
                <div className="space-y-1.5 max-h-36 overflow-y-auto font-mono text-[11px]">
                  {plan.operations.map((op) => {
                    const isBlock = op.action.includes('block') || op.action.includes('prop')
                    return (
                      <div
                        key={op.operationId}
                        className="p-1.5 rounded bg-[#181820] border border-[#2e2e38] flex items-center justify-between"
                      >
                        <div className="flex items-center space-x-1.5">
                          <span className={isBlock ? 'text-blue-400 font-semibold' : 'text-amber-400 font-semibold'}>
                            {op.action}
                          </span>
                          <span
                            className={`text-[9px] px-1 py-0.2 rounded ${
                              isBlock
                                ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                                : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            }`}
                          >
                            {isBlock ? 'block/prop' : 'item'}
                          </span>
                        </div>
                        <span className="text-gray-300">{op.resourceId}</span>
                      </div>
                    )
                  })}
                </div>
              </div>

              <div className="flex justify-end space-x-2">
                <button
                  onClick={onClose}
                  className="px-3 py-2 text-xs rounded-lg text-gray-400 hover:bg-[#25252e]"
                >
                  Cancel
                </button>
                <button
                  onClick={handleApprovePlan}
                  disabled={step === 'approving'}
                  className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold rounded-lg shadow transition flex items-center space-x-1.5"
                >
                  {step === 'approving' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                  <span>Approve Plan</span>
                </button>
              </div>
            </div>
          )}

          {(step === 'approved' || step === 'deploying') && (
            <div className="text-center py-6 space-y-4">
              <div className="p-3 bg-amber-950/20 border border-amber-800/40 rounded-xl text-xs text-amber-300">
                Plan approved! Ready to dispatch allowlisted operations to the server over WebSocket.
              </div>
              <button
                onClick={handleExecute}
                disabled={step === 'deploying'}
                className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-lg transition flex items-center space-x-2 mx-auto"
              >
                {step === 'deploying' ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Applying on Paper 1.21 Server...</span>
                  </>
                ) : (
                  <>
                    <Rocket className="w-4 h-4" />
                    <span>Deploy to Live Server</span>
                  </>
                )}
              </button>
            </div>
          )}

          {step === 'done' && executionResult && (
            <div className="text-center py-4 space-y-4">
              <div className="w-12 h-12 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-gray-100">
                  Revision #{currentRevision?.revision_number || ''} Applied Successfully!
                </h4>
                <p className="text-xs text-gray-400 mt-1">
                  Definitions compiled and synchronized to {selectedTargetId || targetId}.
                </p>
              </div>
              <div className="p-3 bg-[#111114] border border-[#25252e] rounded-xl text-left text-xs font-mono space-y-1">
                <div className="text-gray-500">In-Game Verification:</div>
                <div className="text-emerald-400 bg-[#0e0e11] p-2 rounded border border-[#22222a]">
                  /mcp give {plan?.operations[0]?.resourceId || 'item_id'}
                </div>
              </div>
              <button
                onClick={onClose}
                className="px-5 py-2 bg-[#272730] hover:bg-[#32323e] text-gray-200 text-xs font-medium rounded-lg transition"
              >
                Close
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
