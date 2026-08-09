export interface LogicRecommendation {
  Logic_Name: string;
  Logic_Expression: string;
  Specificity: number;
  Selectivity: number;
  Complexity: string;
  Description: string;
}

export type LogicMatrix = Record<string, LogicRecommendation>;

function hashKey(tCount: number, hCount: number): string {
  return `${tCount}_${hCount}`;
}

const dualLogicData: LogicMatrix = {
  [hashKey(1, 0)]: { Logic_Name: "Single_Target", Logic_Expression: "T1", Specificity: 2, Selectivity: 1, Complexity: "Low", Description: "Basic CAR targeting" },
  [hashKey(1, 1)]: { Logic_Name: "Single_Veto", Logic_Expression: "T1 AND NOT(H1)", Specificity: 4, Selectivity: 5, Complexity: "Low", Description: "Healthy protection" },
  [hashKey(1, 2)]: { Logic_Name: "Veto_OR", Logic_Expression: "T1 AND NOT(H1 OR H2)", Specificity: 4, Selectivity: 5, Complexity: "Medium", Description: "Two healthy veto" },
  [hashKey(1, 3)]: { Logic_Name: "Triple_Veto", Logic_Expression: "T1 AND NOT(H1 OR H2 OR H3)", Specificity: 4, Selectivity: 5, Complexity: "Medium", Description: "Strong safety" },
  [hashKey(1, 4)]: { Logic_Name: "Quad_Veto", Logic_Expression: "T1 AND NOT(H1 OR H2 OR H3 OR H4)", Specificity: 4, Selectivity: 5, Complexity: "Medium", Description: "Healthy veto" },
  [hashKey(1, 5)]: { Logic_Name: "Max_Veto", Logic_Expression: "T1 AND NOT(H1 OR H2 OR H3 OR H4 OR H5)", Specificity: 4, Selectivity: 5, Complexity: "Medium", Description: "Maximum safety" },

  [hashKey(2, 0)]: { Logic_Name: "AND_Gate", Logic_Expression: "T1 AND T2", Specificity: 5, Selectivity: 3, Complexity: "Low", Description: "Tumor co-expression targeting" },
  [hashKey(2, 1)]: { Logic_Name: "AND_Veto", Logic_Expression: "(T1 AND T2) AND NOT(H1)", Specificity: 5, Selectivity: 5, Complexity: "Medium", Description: "High specificity" },
  [hashKey(2, 2)]: { Logic_Name: "AND_Dual_Veto", Logic_Expression: "(T1 AND T2) AND NOT(H1 OR H2)", Specificity: 5, Selectivity: 5, Complexity: "Medium", Description: "Healthy veto" },
  [hashKey(2, 3)]: { Logic_Name: "AND_Triple_Veto", Logic_Expression: "(T1 AND T2) AND NOT(H1 OR H2 OR H3)", Specificity: 5, Selectivity: 5, Complexity: "Medium", Description: "High safety" },
  [hashKey(2, 4)]: { Logic_Name: "AND_Quad_Veto", Logic_Expression: "(T1 AND T2) AND NOT(H1 OR H2 OR H3 OR H4)", Specificity: 5, Selectivity: 5, Complexity: "Medium", Description: "Strong safety" },
  [hashKey(2, 5)]: { Logic_Name: "AND_Max_Veto", Logic_Expression: "(T1 AND T2) AND NOT(H1 OR H2 OR H3 OR H4 OR H5)", Specificity: 5, Selectivity: 5, Complexity: "Medium", Description: "Maximum protection" },

  [hashKey(3, 0)]: { Logic_Name: "OR_Redundancy", Logic_Expression: "T1 OR T2 OR T3", Specificity: 3, Selectivity: 2, Complexity: "Low", Description: "Tumor heterogeneity" },
  [hashKey(3, 1)]: { Logic_Name: "OR_Veto", Logic_Expression: "(T1 OR T2 OR T3) AND NOT(H1)", Specificity: 4, Selectivity: 4, Complexity: "Medium", Description: "Balanced detection" },
  [hashKey(3, 2)]: { Logic_Name: "OR_Dual_Veto", Logic_Expression: "(T1 OR T2 OR T3) AND NOT(H1 OR H2)", Specificity: 4, Selectivity: 5, Complexity: "Medium", Description: "Improved safety" },
  [hashKey(3, 3)]: { Logic_Name: "OR_Triple_Veto", Logic_Expression: "(T1 OR T2 OR T3) AND NOT(H1 OR H2 OR H3)", Specificity: 4, Selectivity: 5, Complexity: "Medium", Description: "Strong healthy protection" },
  [hashKey(3, 4)]: { Logic_Name: "OR_Quad_Veto", Logic_Expression: "(T1 OR T2 OR T3) AND NOT(H1 OR H2 OR H3 OR H4)", Specificity: 4, Selectivity: 5, Complexity: "Medium", Description: "Safe design" },
  [hashKey(3, 5)]: { Logic_Name: "OR_Max_Veto", Logic_Expression: "(T1 OR T2 OR T3) AND NOT(H1 OR H2 OR H3 OR H4 OR H5)", Specificity: 4, Selectivity: 5, Complexity: "Medium", Description: "Maximum veto" },

  [hashKey(4, 0)]: { Logic_Name: "Pair_AND", Logic_Expression: "(T1 AND T2) OR (T3 AND T4)", Specificity: 4, Selectivity: 3, Complexity: "Medium", Description: "Subset targeting" },
  [hashKey(4, 1)]: { Logic_Name: "Pair_AND_Veto", Logic_Expression: "((T1 AND T2) OR (T3 AND T4)) AND NOT(H1)", Specificity: 5, Selectivity: 5, Complexity: "Medium", Description: "Selective killing" },
  [hashKey(4, 2)]: { Logic_Name: "Pair_AND_Dual_Veto", Logic_Expression: "((T1 AND T2) OR (T3 AND T4)) AND NOT(H1 OR H2)", Specificity: 5, Selectivity: 5, Complexity: "Medium", Description: "Healthy protection" },
  [hashKey(4, 3)]: { Logic_Name: "Pair_AND_Triple_Veto", Logic_Expression: "((T1 AND T2) OR (T3 AND T4)) AND NOT(H1 OR H2 OR H3)", Specificity: 5, Selectivity: 5, Complexity: "Medium", Description: "High safety" },
  [hashKey(4, 4)]: { Logic_Name: "Pair_AND_Quad_Veto", Logic_Expression: "((T1 AND T2) OR (T3 AND T4)) AND NOT(H1 OR H2 OR H3 OR H4)", Specificity: 5, Selectivity: 5, Complexity: "Medium", Description: "Safe architecture" },
  [hashKey(4, 5)]: { Logic_Name: "Pair_AND_Max_Veto", Logic_Expression: "((T1 AND T2) OR (T3 AND T4)) AND NOT(H1 OR H2 OR H3 OR H4 OR H5)", Specificity: 5, Selectivity: 5, Complexity: "Medium", Description: "Maximum veto" },

  [hashKey(5, 0)]: { Logic_Name: "Distributed_OR", Logic_Expression: "T1 OR T2 OR T3 OR T4 OR T5", Specificity: 3, Selectivity: 2, Complexity: "Low", Description: "Tumor heterogeneity" },
  [hashKey(5, 1)]: { Logic_Name: "OR_Veto5", Logic_Expression: "(T1 OR T2 OR T3 OR T4 OR T5) AND NOT(H1)", Specificity: 4, Selectivity: 4, Complexity: "Medium", Description: "Healthy veto" },
  [hashKey(5, 2)]: { Logic_Name: "OR_Dual_Veto5", Logic_Expression: "(T1 OR T2 OR T3 OR T4 OR T5) AND NOT(H1 OR H2)", Specificity: 4, Selectivity: 5, Complexity: "Medium", Description: "Safe targeting" },
  [hashKey(5, 3)]: { Logic_Name: "OR_Triple_Veto5", Logic_Expression: "(T1 OR T2 OR T3 OR T4 OR T5) AND NOT(H1 OR H2 OR H3)", Specificity: 4, Selectivity: 5, Complexity: "Medium", Description: "Healthy protection" },
  [hashKey(5, 4)]: { Logic_Name: "OR_Quad_Veto5", Logic_Expression: "(T1 OR T2 OR T3 OR T4 OR T5) AND NOT(H1 OR H2 OR H3 OR H4)", Specificity: 4, Selectivity: 5, Complexity: "Medium", Description: "Strong safety" },
  [hashKey(5, 5)]: { Logic_Name: "OR_Max_Veto5", Logic_Expression: "(T1 OR T2 OR T3 OR T4 OR T5) AND NOT(H1 OR H2 OR H3 OR H4 OR H5)", Specificity: 4, Selectivity: 5, Complexity: "Medium", Description: "Maximum protection" },
};

export function getDualLogicRecommendation(tCount: number, hCount: number): LogicRecommendation | null {
  return dualLogicData[hashKey(tCount, hCount)] || null;
}
