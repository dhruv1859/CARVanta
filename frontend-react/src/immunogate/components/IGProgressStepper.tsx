import { Check } from "lucide-react";

interface Step {
  id: number;
  label: string;
  description: string;
}

interface ProgressStepperProps {
  currentStep: number;
  onStepClick?: (step: number) => void;
}

const steps: Step[] = [
  { id: 0, label: "Upload", description: "Upload datasets" },
  { id: 1, label: "Select", description: "Choose biomarkers" },
  { id: 2, label: "Analyze", description: "Generate analysis" },
  { id: 3, label: "Design", description: "CAR-T design" },
  { id: 4, label: "Results", description: "View insights" },
];

export function IGProgressStepper({ currentStep, onStepClick }: ProgressStepperProps) {
  return (
    <nav aria-label="Progress" className="ig-stepper">
      {steps.map((step, index) => {
        const isComplete = currentStep > step.id;
        const isCurrent = currentStep === step.id;
        const isClickable = onStepClick && currentStep >= step.id;

        return (
          <div key={step.id} className="ig-stepper-item">
            {index !== 0 && (
              <div
                className={`ig-stepper-line ${isComplete ? 'active' : ''}`}
                style={{ left: `calc(-50% + 20px)`, right: `calc(50% + 20px)` }}
              />
            )}
            <button
              onClick={() => isClickable && onStepClick(step.id)}
              disabled={!isClickable}
              className={`ig-step-circle ${isComplete ? 'complete' : isCurrent ? 'current' : 'inactive'}`}
              data-testid={`step-${step.id}`}
            >
              {isComplete ? <Check size={18} /> : <span>{step.id}</span>}
            </button>
            <div className="ig-step-label">
              <p className={`ig-step-label-text ${isCurrent ? '' : 'ig-text-muted'}`}>{step.label}</p>
              <p className="ig-step-label-desc ig-text-xs">{step.description}</p>
            </div>
          </div>
        );
      })}
    </nav>
  );
}
