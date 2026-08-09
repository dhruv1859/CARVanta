import { getDualLogicRecommendation, LogicRecommendation } from "./dualLogicModel";
import { getMultiLogicRecommendation } from "./multiLogicModel";

export type LogicType = 'dual' | 'multi';

export function recommendLogic(tumorCount: number, healthyCount: number, logicType: LogicType): LogicRecommendation | null {
  const tCount = Math.max(1, Math.min(5, tumorCount));
  const hCount = Math.max(0, Math.min(5, healthyCount));
  if (logicType === 'dual') {
    return getDualLogicRecommendation(tCount, hCount);
  } else {
    return getMultiLogicRecommendation(tCount, hCount);
  }
}

export function mapLogicExpressionToAntigens(
  expression: string,
  tumorAntigens: string[],
  healthyAntigens: string[]
): string {
  let mappedExpression = expression;
  tumorAntigens.forEach((antigen, index) => {
    const tVar = new RegExp(`\\bT${index + 1}\\b`, 'g');
    mappedExpression = mappedExpression.replace(tVar, antigen);
  });
  healthyAntigens.forEach((antigen, index) => {
    const hVar = new RegExp(`\\bH${index + 1}\\b`, 'g');
    mappedExpression = mappedExpression.replace(hVar, antigen);
  });
  return mappedExpression;
}
