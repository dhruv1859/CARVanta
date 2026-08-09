import { LogicRecommendation } from "./dualLogicModel";

export type LogicMatrix = Record<string, LogicRecommendation>;

function hashKey(tCount: number, hCount: number): string {
  return `${tCount}_${hCount}`;
}

const multiLogicData: LogicMatrix = {
  [hashKey(1, 0)]: { Logic_Name: "Single_Target", Logic_Expression: "T1", Specificity: 2, Selectivity: 1, Complexity: "Low", Description: "Basic activation" },
  [hashKey(1, 1)]: { Logic_Name: "Single_Veto", Logic_Expression: "T1 AND NOT(H1)", Specificity: 4, Selectivity: 5, Complexity: "Medium", Description: "Healthy protection" },
  [hashKey(1, 2)]: { Logic_Name: "Dual_Veto", Logic_Expression: "T1 AND NOT(H1) AND NOT(H2)", Specificity: 4, Selectivity: 5, Complexity: "Medium", Description: "Two veto safety" },
  [hashKey(1, 3)]: { Logic_Name: "Triple_Veto", Logic_Expression: "T1 AND NOT(H1) AND NOT(H2) AND NOT(H3)", Specificity: 4, Selectivity: 5, Complexity: "Medium", Description: "Strong protection" },
  [hashKey(1, 4)]: { Logic_Name: "Quad_Veto", Logic_Expression: "T1 AND NOT(H1) AND NOT(H2) AND NOT(H3) AND NOT(H4)", Specificity: 4, Selectivity: 5, Complexity: "Medium", Description: "Safe design" },
  [hashKey(1, 5)]: { Logic_Name: "Max_Veto", Logic_Expression: "T1 AND NOT(H1) AND NOT(H2) AND NOT(H3) AND NOT(H4) AND NOT(H5)", Specificity: 4, Selectivity: 5, Complexity: "Medium", Description: "Maximum safety" },

  [hashKey(2, 0)]: { Logic_Name: "Strong_AND", Logic_Expression: "T1 AND T2", Specificity: 5, Selectivity: 3, Complexity: "Low", Description: "Co-expression targeting" },
  [hashKey(2, 1)]: { Logic_Name: "AND_Veto", Logic_Expression: "T1 AND T2 AND NOT(H1)", Specificity: 5, Selectivity: 5, Complexity: "Medium", Description: "High specificity" },
  [hashKey(2, 2)]: { Logic_Name: "Double_Veto", Logic_Expression: "T1 AND T2 AND NOT(H1) AND NOT(H2)", Specificity: 5, Selectivity: 5, Complexity: "Medium", Description: "Healthy protection" },
  [hashKey(2, 3)]: { Logic_Name: "Triple_Veto", Logic_Expression: "T1 AND T2 AND NOT(H1) AND NOT(H2) AND NOT(H3)", Specificity: 5, Selectivity: 5, Complexity: "High", Description: "Strong safety" },
  [hashKey(2, 4)]: { Logic_Name: "Quad_Veto", Logic_Expression: "T1 AND T2 AND NOT(H1) AND NOT(H2) AND NOT(H3) AND NOT(H4)", Specificity: 5, Selectivity: 5, Complexity: "High", Description: "Maximum safety" },
  [hashKey(2, 5)]: { Logic_Name: "Max_Veto", Logic_Expression: "T1 AND T2 AND NOT(H1) AND NOT(H2) AND NOT(H3) AND NOT(H4) AND NOT(H5)", Specificity: 5, Selectivity: 5, Complexity: "High", Description: "Maximum protection" },

  [hashKey(3, 0)]: { Logic_Name: "Triple_AND", Logic_Expression: "T1 AND T2 AND T3", Specificity: 5, Selectivity: 4, Complexity: "Medium", Description: "Highly specific" },
  [hashKey(3, 1)]: { Logic_Name: "Triple_AND_Veto", Logic_Expression: "T1 AND T2 AND T3 AND NOT(H1)", Specificity: 5, Selectivity: 5, Complexity: "High", Description: "Selective killing" },
  [hashKey(3, 2)]: { Logic_Name: "Triple_Dual_Veto", Logic_Expression: "T1 AND T2 AND T3 AND NOT(H1) AND NOT(H2)", Specificity: 5, Selectivity: 5, Complexity: "High", Description: "Healthy protection" },
  [hashKey(3, 3)]: { Logic_Name: "Triple_Triple_Veto", Logic_Expression: "T1 AND T2 AND T3 AND NOT(H1) AND NOT(H2) AND NOT(H3)", Specificity: 5, Selectivity: 5, Complexity: "High", Description: "Strong safety" },
  [hashKey(3, 4)]: { Logic_Name: "Triple_Quad_Veto", Logic_Expression: "T1 AND T2 AND T3 AND NOT(H1) AND NOT(H2) AND NOT(H3) AND NOT(H4)", Specificity: 5, Selectivity: 5, Complexity: "VeryHigh", Description: "Safe design" },
  [hashKey(3, 5)]: { Logic_Name: "Triple_Max_Veto", Logic_Expression: "T1 AND T2 AND T3 AND NOT(H1) AND NOT(H2) AND NOT(H3) AND NOT(H4) AND NOT(H5)", Specificity: 5, Selectivity: 5, Complexity: "VeryHigh", Description: "Maximum veto" },

  [hashKey(4, 0)]: { Logic_Name: "Quad_AND", Logic_Expression: "T1 AND T2 AND T3 AND T4", Specificity: 5, Selectivity: 4, Complexity: "High", Description: "Extremely specific" },
  [hashKey(4, 1)]: { Logic_Name: "Quad_AND_Veto", Logic_Expression: "T1 AND T2 AND T3 AND T4 AND NOT(H1)", Specificity: 5, Selectivity: 5, Complexity: "High", Description: "Selective killing" },
  [hashKey(4, 2)]: { Logic_Name: "Quad_Dual_Veto", Logic_Expression: "T1 AND T2 AND T3 AND T4 AND NOT(H1) AND NOT(H2)", Specificity: 5, Selectivity: 5, Complexity: "High", Description: "Healthy protection" },
  [hashKey(4, 3)]: { Logic_Name: "Quad_Triple_Veto", Logic_Expression: "T1 AND T2 AND T3 AND T4 AND NOT(H1) AND NOT(H2) AND NOT(H3)", Specificity: 5, Selectivity: 5, Complexity: "VeryHigh", Description: "Strong safety" },
  [hashKey(4, 4)]: { Logic_Name: "Quad_Quad_Veto", Logic_Expression: "T1 AND T2 AND T3 AND T4 AND NOT(H1) AND NOT(H2) AND NOT(H3) AND NOT(H4)", Specificity: 5, Selectivity: 5, Complexity: "VeryHigh", Description: "Safe system" },
  [hashKey(4, 5)]: { Logic_Name: "Quad_Max_Veto", Logic_Expression: "T1 AND T2 AND T3 AND T4 AND NOT(H1) AND NOT(H2) AND NOT(H3) AND NOT(H4) AND NOT(H5)", Specificity: 5, Selectivity: 5, Complexity: "VeryHigh", Description: "Maximum safety" },

  [hashKey(5, 0)]: { Logic_Name: "Full_AND", Logic_Expression: "T1 AND T2 AND T3 AND T4 AND T5", Specificity: 5, Selectivity: 4, Complexity: "VeryHigh", Description: "Extreme specificity" },
  [hashKey(5, 1)]: { Logic_Name: "Full_AND_Veto", Logic_Expression: "T1 AND T2 AND T3 AND T4 AND T5 AND NOT(H1)", Specificity: 5, Selectivity: 5, Complexity: "VeryHigh", Description: "Selective targeting" },
  [hashKey(5, 2)]: { Logic_Name: "Full_Dual_Veto", Logic_Expression: "T1 AND T2 AND T3 AND T4 AND T5 AND NOT(H1) AND NOT(H2)", Specificity: 5, Selectivity: 5, Complexity: "VeryHigh", Description: "Healthy protection" },
  [hashKey(5, 3)]: { Logic_Name: "Full_Triple_Veto", Logic_Expression: "T1 AND T2 AND T3 AND T4 AND T5 AND NOT(H1) AND NOT(H2) AND NOT(H3)", Specificity: 5, Selectivity: 5, Complexity: "VeryHigh", Description: "Safe architecture" },
  [hashKey(5, 4)]: { Logic_Name: "Full_Quad_Veto", Logic_Expression: "T1 AND T2 AND T3 AND T4 AND T5 AND NOT(H1) AND NOT(H2) AND NOT(H3) AND NOT(H4)", Specificity: 5, Selectivity: 5, Complexity: "VeryHigh", Description: "High safety" },
  [hashKey(5, 5)]: { Logic_Name: "Full_Max_Veto", Logic_Expression: "T1 AND T2 AND T3 AND T4 AND T5 AND NOT(H1) AND NOT(H2) AND NOT(H3) AND NOT(H4) AND NOT(H5)", Specificity: 5, Selectivity: 5, Complexity: "VeryHigh", Description: "Maximum protection" },
};

export function getMultiLogicRecommendation(tCount: number, hCount: number): LogicRecommendation | null {
  return multiLogicData[hashKey(tCount, hCount)] || null;
}
