// BrainBench - All Hardcoded Benchmark Data
// Source: analysis_results.xlsx (Generated 2026-02-22)

const MODELS = {
  gemma: {
    id: 'gemma',
    name: 'Gemma3:4b',
    developer: 'Google',
    parameters: '4B',
    color: '#3b82f6',
    colorRgb: '59, 130, 246',
  },
  phi: {
    id: 'phi',
    name: 'Phi3:3.8b',
    developer: 'Microsoft',
    parameters: '3.8B',
    color: '#a855f7',
    colorRgb: '168, 85, 247',
  },
  qwen: {
    id: 'qwen',
    name: 'Qwen3:4b',
    developer: 'Alibaba',
    parameters: '4B',
    color: '#f59e0b',
    colorRgb: '245, 158, 11',
  }
};

const MODEL_ORDER = ['gemma', 'phi', 'qwen'];

// ===== EXECUTIVE SUMMARY =====
const EXECUTIVE_SUMMARY = {
  totalQuestionsPerModel: 2544,
  overall: {
    gemma: { correct: 1624, accuracy: 0.6384, totalTime: 18581.58, avgTime: 7.304, medianTime: 6.434 },
    phi:   { correct: 846,  accuracy: 0.3325, totalTime: 13809.47, avgTime: 5.428, medianTime: 5.183 },
    qwen:  { correct: 1687, accuracy: 0.6631, totalTime: 65619.89, avgTime: 25.794, medianTime: 24.239 },
  }
};

// ===== CATEGORY COMPARISON =====
const CATEGORIES = {
  probStats: {
    name: 'Advanced Probability & Statistics',
    shortName: 'Prob & Stats',
    questions: 1000,
    results: {
      gemma: { correct: 859, incorrect: 141, accuracy: 0.859, avgTime: 8.369, medianTime: 6.796, minTime: 2.375, maxTime: 1213.042 },
      phi:   { correct: 382, incorrect: 618, accuracy: 0.382, avgTime: 5.552, medianTime: 5.258, minTime: 2.074, maxTime: 19.503 },
      qwen:  { correct: 742, incorrect: 258, accuracy: 0.742, avgTime: 26.092, medianTime: 24.226, minTime: 11.773, maxTime: 39.191 },
    }
  },
  calculus: {
    name: 'Calculus I',
    shortName: 'Calculus I',
    questions: 900,
    results: {
      gemma: { correct: 623, incorrect: 277, accuracy: 0.6922, avgTime: 6.620, medianTime: 6.206, minTime: 4.188, maxTime: 21.525 },
      phi:   { correct: 385, incorrect: 515, accuracy: 0.4278, avgTime: 5.190, medianTime: 5.073, minTime: 2.776, maxTime: 19.190 },
      qwen:  { correct: 760, incorrect: 140, accuracy: 0.8444, avgTime: 24.888, medianTime: 23.754, minTime: 12.717, maxTime: 40.572 },
    }
  },
  grade8: {
    name: 'Grade 8 Math',
    shortName: 'Grade 8',
    questions: 644,
    results: {
      gemma: { correct: 142, incorrect: 502, accuracy: 0.2205, avgTime: 6.606, medianTime: 6.131, minTime: 2.987, maxTime: 21.987 },
      phi:   { correct: 79,  incorrect: 565, accuracy: 0.1227, avgTime: 5.570, medianTime: 5.224, minTime: 2.959, maxTime: 19.216 },
      qwen:  { correct: 185, incorrect: 459, accuracy: 0.2873, avgTime: 26.598, medianTime: 26.261, minTime: 10.001, maxTime: 38.482 },
    }
  }
};

const CATEGORY_ORDER = ['probStats', 'calculus', 'grade8'];

// ===== CALCULUS I TOPIC BREAKDOWN =====
const CALCULUS_TOPICS = [
  { topic: 'Evaluate the limit',              count: 120, gemma: 1.0,    phi: 0.7333, qwen: 0.975  },
  { topic: 'Evaluate limit (factoring)',       count: 30,  gemma: 1.0,    phi: 0.5333, qwen: 1.0    },
  { topic: 'Tangent line slope',               count: 40,  gemma: 0.975,  phi: 0.275,  qwen: 1.0    },
  { topic: 'Definite integral',                count: 100, gemma: 0.93,   phi: 0.33,   qwen: 0.91   },
  { topic: 'Indefinite integral',              count: 150, gemma: 0.92,   phi: 0.3733, qwen: 0.9933 },
  { topic: 'Power rule derivative',            count: 100, gemma: 0.78,   phi: 0.77,   qwen: 0.98   },
  { topic: 'Find the derivative',              count: 80,  gemma: 0.7375, phi: 0.7375, qwen: 0.6875 },
  { topic: 'Chain rule derivative',            count: 70,  gemma: 0.5571, phi: 0.4714, qwen: 0.5714 },
  { topic: 'Critical points',                  count: 70,  gemma: 0.3571, phi: 0.1429, qwen: 0.8571 },
  { topic: 'Related rates',                    count: 40,  gemma: 0.05,   phi: 0.025,  qwen: 0.85   },
  { topic: 'Product rule derivative',          count: 60,  gemma: 0.0,    phi: 0.0,    qwen: 0.7667 },
  { topic: 'Quotient rule derivative',         count: 40,  gemma: 0.0,    phi: 0.025,  qwen: 0.0    },
];

// ===== PROB & STATS TOPIC BREAKDOWN =====
const PROB_STATS_TOPICS = [
  { topic: 'Combinations C(n,r)',              count: 150, gemma: 0.9867, phi: 0.36,   qwen: 0.9133 },
  { topic: 'Permutations P(n,r)',              count: 100, gemma: 0.98,   phi: 0.34,   qwen: 0.98   },
  { topic: 'Conditional Probability',          count: 150, gemma: 0.98,   phi: 0.5533, qwen: 0.98   },
  { topic: 'Probability (favorable/total)',    count: 50,  gemma: 0.98,   phi: 0.46,   qwen: 0.96   },
  { topic: 'Combination formula',              count: 150, gemma: 0.9667, phi: 0.52,   qwen: 0.90   },
  { topic: 'Variance',                         count: 100, gemma: 0.85,   phi: 0.21,   qwen: 0.48   },
  { topic: 'Expected value',                   count: 150, gemma: 0.68,   phi: 0.1133, qwen: 0.3067 },
  { topic: 'Z-score calculation',              count: 150, gemma: 0.5667, phi: 0.48,   qwen: 0.5533 },
];

// ===== GRADE 8 MATH SUBCATEGORY BREAKDOWN =====
const GRADE8_TOPICS = [
  { topic: 'Statistics & Probability',     count: 60,  gemma: 0.55,   phi: 0.20,   qwen: 0.5667 },
  { topic: 'Expressions & Equations',      count: 186, gemma: 0.2688, phi: 0.2258, qwen: 0.4086 },
  { topic: 'The Number System',            count: 164, gemma: 0.2256, phi: 0.1037, qwen: 0.2378 },
  { topic: 'Geometry',                     count: 145, gemma: 0.1517, phi: 0.0414, qwen: 0.2207 },
  { topic: 'Functions',                    count: 88,  gemma: 0.0,    phi: 0.0227, qwen: 0.0341 },
];

// ===== VERIFICATION ANALYSIS =====
const VERIFICATION = {
  matchTypes: {
    gemma: { exact: 55.74, equivalent: 7.19, tolerance: 0.90, no_match: 13.76, type_mismatch: 21.74, extraction_failed: 0.04, unknown: 0.63 },
    phi:   { exact: 28.03, equivalent: 4.80, tolerance: 0.43, no_match: 19.06, type_mismatch: 46.23, extraction_failed: 0.04, unknown: 1.42 },
    qwen:  { exact: 50.55, equivalent: 13.01, tolerance: 2.75, no_match: 9.55, type_mismatch: 14.31, extraction_failed: 0.43, unknown: 9.39 },
  },
  confidence: {
    gemma: { extraction: 0.9977, comparison: 0.9847 },
    phi:   { extraction: 0.9789, comparison: 0.9807 },
    qwen:  { extraction: 0.8629, comparison: 0.8822 },
  },
  status: {
    gemma: { correct: 63.84, incorrect: 36.12, unable: 0.04, unknown: 0.0 },
    phi:   { correct: 33.25, incorrect: 66.71, unable: 0.04, unknown: 0.0 },
    qwen:  { correct: 66.31, incorrect: 24.61, unable: 0.43, unknown: 8.65 },
  }
};

// ===== TIMING ANALYSIS =====
const TIMING = {
  byCategory: {
    probStats: {
      gemma: { count: 1000, mean: 8.369, median: 6.796, stdDev: 39.319, p25: 5.388, p75: 7.865, p95: 9.594, min: 2.375, max: 1213.042 },
      phi:   { count: 1000, mean: 5.552, median: 5.258, stdDev: 1.854, p25: 4.500, p75: 6.052, p95: 7.999, min: 2.074, max: 19.503 },
      qwen:  { count: 1000, mean: 26.092, median: 24.226, stdDev: 7.615, p25: 20.068, p75: 33.576, p95: 37.837, min: 11.773, max: 39.191 },
    },
    calculus: {
      gemma: { count: 900, mean: 6.620, median: 6.206, stdDev: 1.620, p25: 5.543, p75: 7.303, p95: 9.405, min: 4.188, max: 21.525 },
      phi:   { count: 900, mean: 5.190, median: 5.073, stdDev: 1.144, p25: 4.506, p75: 5.739, p95: 6.878, min: 2.776, max: 19.190 },
      qwen:  { count: 900, mean: 24.888, median: 23.754, stdDev: 6.241, p25: 20.059, p75: 28.868, p95: 37.279, min: 12.717, max: 40.572 },
    },
    grade8: {
      gemma: { count: 644, mean: 6.606, median: 6.131, stdDev: 2.264, p25: 5.371, p75: 7.272, p95: 9.839, min: 2.987, max: 21.987 },
      phi:   { count: 644, mean: 5.570, median: 5.224, stdDev: 1.746, p25: 4.561, p75: 6.124, p95: 8.228, min: 2.959, max: 19.216 },
      qwen:  { count: 644, mean: 26.598, median: 26.261, stdDev: 9.203, p25: 18.287, p75: 37.178, p95: 37.716, min: 10.001, max: 38.482 },
    }
  },
  overall: {
    gemma: { totalQuestions: 2544, totalTime: 18581.58, totalMinutes: 309.69, avgTime: 7.304, medianTime: 6.434 },
    phi:   { totalQuestions: 2544, totalTime: 13809.47, totalMinutes: 230.16, avgTime: 5.428, medianTime: 5.183 },
    qwen:  { totalQuestions: 2544, totalTime: 65619.89, totalMinutes: 1093.66, avgTime: 25.794, medianTime: 24.239 },
  }
};

// ===== TOPIC TIMING DATA (avg seconds per question per topic) =====
const CALCULUS_TIMING = [
  { topic: 'Evaluate the limit',       gemma: 5.628, phi: 4.486, qwen: 24.652 },
  { topic: 'Evaluate limit (factoring)', gemma: 7.181, phi: 4.630, qwen: 25.209 },
  { topic: 'Tangent line slope',        gemma: 6.401, phi: 5.230, qwen: 23.378 },
  { topic: 'Definite integral',         gemma: 7.258, phi: 5.817, qwen: 26.718 },
  { topic: 'Indefinite integral',       gemma: 5.575, phi: 5.340, qwen: 17.943 },
  { topic: 'Power rule derivative',     gemma: 7.657, phi: 4.777, qwen: 26.408 },
  { topic: 'Find the derivative',       gemma: 6.897, phi: 5.309, qwen: 28.974 },
  { topic: 'Chain rule derivative',     gemma: 6.644, phi: 5.395, qwen: 31.313 },
  { topic: 'Critical points',           gemma: 6.710, phi: 5.332, qwen: 21.698 },
  { topic: 'Related rates',             gemma: 8.127, phi: 6.002, qwen: 32.096 },
  { topic: 'Product rule derivative',   gemma: 7.289, phi: 5.205, qwen: 24.669 },
  { topic: 'Quotient rule derivative',  gemma: 5.862, phi: 4.900, qwen: 23.821 },
];

// Helper functions
function pct(value) {
  return (value * 100).toFixed(1) + '%';
}

function pctNum(value) {
  return parseFloat((value * 100).toFixed(1));
}
