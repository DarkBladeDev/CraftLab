import { useState } from 'react'
import { Rocket, CheckCircle2, AlertTriangle, X, Loader2 } from 'lucide-react'
import {
  createDeploymentPlan,
  approveDeploymentPlan,
  executeDeploymentPlan,
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
  const [step, setStep] = useState<'idle' | 'planning' | 'planned' | 'approving' | 'approved' | 'deploying' | 'done'>('idle')
  const [plan, setPlan] = useState<DeploymentPlan | null>(null)
  const [executionResult, setExecutionResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const handleCreatePlan = async () => {
    if (!revisionId || !targetId) {
      setError('Please select both a revision and a target server.')
      return
    }
    setError(null)
    setStep('planning')
    try {
      const generated = await createDeploymentPlan(revisionId, targetId)
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
            <h3 className="font-semibold text-gray-100 text-base">Release & Deployment Pipeline</h3>
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

          {/* Target and Revision context */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 bg-[#131317] border border-[#272730] rounded-lg">
              <div className="text-gray-500 mb-1">Target Server</div>
              <div className="font-medium text-gray-200 font-mono">{targetId || 'None Selected'}</div>
            </div>
            <div className="p-3 bg-[#131317] border border-[#272730] rounded-lg">
              <div className="text-gray-500 mb-1">Project Revision</div>
              <div className="font-medium text-emerald-400 font-mono">{revisionId || 'None Selected'}</div>
            </div>
          </div>

          {/* Stepper view */}
          {step === 'idle' && (
            <div className="text-center py-6 space-y-3">
              <p className="text-xs text-gray-400">
                Ready to compile deployment plan. Comparing canonical revision against target state.
              </p>
              <button
                onClick={handleCreatePlan}
                disabled={!revisionId || !targetId}
                className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow transition"
              >
                Generate Deployment Plan
              </button>
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
                  <span className="text-gray-400">Plan Hash:</span>
                  <span className="font-mono text-gray-300">{plan.plan_hash.slice(0, 16)}...</span>
                </div>
                <div className="font-semibold text-gray-300 mb-2">Operations ({plan.operations.length}):</div>
                <div className="space-y-1.5 max-h-36 overflow-y-auto font-mono text-[11px]">
                  {plan.operations.map((op) => (
                    <div
                      key={op.operationId}
                      className="p-1.5 rounded bg-[#181820] border border-[#2e2e38] flex items-center justify-between"
                    >
                      <span className="text-amber-400">{op.action}</span>
                      <span className="text-gray-300">{op.resourceId}</span>
                    </div>
                  ))}
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
                <h4 className="text-sm font-semibold text-gray-100">Deployment Applied Successfully!</h4>
                <p className="text-xs text-gray-400 mt-1">
                  Item definition was compiled and saved to local Paper storage.
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
