import { z } from "zod";

// Biomarker schema
export const biomarkerSchema = z.object({
  name: z.string(),
  category: z.string(),
  indication: z.string(),
});

export type Biomarker = z.infer<typeof biomarkerSchema>;

// Multi-gate logic schema
export const multiGateLogicSchema = z.object({
  tumorCount: z.number().optional(),
  healthyCount: z.number().optional(),
  bestLogic: z.string(),
  logicName: z.string().optional(),
  working: z.string().optional(),
  reason: z.string().optional(),
  description: z.string().optional(),
  rawExpression: z.string().optional(),
  specificity: z.number().min(1).max(5),
  selectivity: z.number().min(1).max(5),
});

export type MultiGateLogic = z.infer<typeof multiGateLogicSchema>;

// Selected biomarkers schema
export const selectedBiomarkersSchema = z.object({
  tumor: z.array(biomarkerSchema).min(1).max(5),
  healthy: z.array(biomarkerSchema).min(0).max(5),
});

export type SelectedBiomarkers = z.infer<typeof selectedBiomarkersSchema>;

// Truth table entry schema
export const truthTableEntrySchema = z.object({
  combination: z.string(),
  tumorState: z.array(z.boolean()),
  healthyState: z.array(z.boolean()),
  carTActive: z.boolean(),
  status: z.enum(["Active/KILL", "Inactive/OFF"]),
  offTarget: z.number(),
  cytokineToxicity: z.number(),
  riskLevel: z.enum(["Safe", "Moderate", "High"]),
});

export type TruthTableEntry = z.infer<typeof truthTableEntrySchema>;
