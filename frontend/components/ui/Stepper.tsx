'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle2, ChevronRight, ChevronLeft } from 'lucide-react'
import './Stepper.css'

export interface StepProps {
  children?: React.ReactNode
  title?: string
  subtitle?: string
  status?: 'completed' | 'current' | 'pending'
}

export function Step({ children }: StepProps) {
  return <div className="stepper-step-content">{children}</div>
}

export interface StepperProps {
  children: React.ReactNode
  initialStep?: number
  currentStep?: number
  onStepChange?: (step: number) => void
  onFinalStepCompleted?: () => void
  backButtonText?: string
  nextButtonText?: string
  showNavigationControls?: boolean
  className?: string
}

export default function Stepper({
  children,
  initialStep = 1,
  currentStep: controlledStep,
  onStepChange,
  onFinalStepCompleted,
  backButtonText = 'Previous',
  nextButtonText = 'Next',
  showNavigationControls = false,
  className = '',
}: StepperProps) {
  const steps = React.Children.toArray(children).filter(
    React.isValidElement
  ) as React.ReactElement<StepProps>[]

  const [internalStep, setInternalStep] = useState(initialStep)
  const activeStep = controlledStep !== undefined ? controlledStep : internalStep
  const totalSteps = steps.length

  const handleStepClick = (stepIndex: number) => {
    const nextVal = stepIndex + 1
    if (controlledStep === undefined) {
      setInternalStep(nextVal)
    }
    onStepChange?.(nextVal)
    if (nextVal === totalSteps) {
      onFinalStepCompleted?.()
    }
  }

  const handlePrev = () => {
    if (activeStep > 1) {
      const nextVal = activeStep - 1
      if (controlledStep === undefined) setInternalStep(nextVal)
      onStepChange?.(nextVal)
    }
  }

  const handleNext = () => {
    if (activeStep < totalSteps) {
      const nextVal = activeStep + 1
      if (controlledStep === undefined) setInternalStep(nextVal)
      onStepChange?.(nextVal)
      if (nextVal === totalSteps) {
        onFinalStepCompleted?.()
      }
    }
  }

  const currentStepElement = steps[activeStep - 1]

  return (
    <div className={`stepper-root ${className}`}>
      {/* Step Header Track */}
      <div className="stepper-header" role="tablist" aria-label="Signal lifecycle steps">
        {steps.map((step, idx) => {
          const stepNumber = idx + 1
          const isCompleted = stepNumber < activeStep || step.props.status === 'completed'
          const isCurrent = stepNumber === activeStep || (step.props.status === 'current' && !isCompleted)
          const stepTitle = step.props.title || `Stage ${stepNumber}`

          return (
            <div key={idx} className="stepper-item-wrapper">
              <button
                type="button"
                role="tab"
                aria-selected={isCurrent}
                aria-label={`${stepTitle} (Step ${stepNumber} of ${totalSteps})`}
                onClick={() => handleStepClick(idx)}
                className={`stepper-node ${isCompleted ? 'node-completed' : ''} ${
                  isCurrent ? 'node-current' : ''
                } ${!isCompleted && !isCurrent ? 'node-pending' : ''}`}
              >
                <span className="stepper-icon-badge">
                  {isCompleted ? (
                    <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
                  ) : (
                    <span className="stepper-number font-mono">{stepNumber}</span>
                  )}
                </span>
                <span className="stepper-label-container">
                  <span className="stepper-title">{stepTitle}</span>
                  {step.props.subtitle && (
                    <span className="stepper-subtitle">{step.props.subtitle}</span>
                  )}
                </span>
              </button>

              {idx < totalSteps - 1 && (
                <div
                  className={`stepper-connector ${
                    stepNumber < activeStep ? 'connector-completed' : 'connector-pending'
                  }`}
                  aria-hidden="true"
                />
              )}
            </div>
          )
        })}
      </div>

      {/* Active Step Content */}
      <div className="stepper-body">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeStep}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.2 }}
            className="stepper-content-panel"
            role="tabpanel"
          >
            {currentStepElement}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Navigation Controls (if enabled) */}
      {showNavigationControls && (
        <div className="stepper-controls">
          <button
            type="button"
            onClick={handlePrev}
            disabled={activeStep <= 1}
            className="stepper-nav-button"
          >
            <ChevronLeft size={14} />
            <span>{backButtonText}</span>
          </button>
          <button
            type="button"
            onClick={handleNext}
            disabled={activeStep >= totalSteps}
            className="stepper-nav-button stepper-nav-primary"
          >
            <span>{nextButtonText}</span>
            <ChevronRight size={14} />
          </button>
        </div>
      )}
    </div>
  )
}
