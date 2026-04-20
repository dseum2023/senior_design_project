// BrainBench - Shared Chart Configuration & Helpers (Enhanced)

// Set Chart.js dark theme defaults
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = 'rgba(51, 65, 85, 0.4)';
Chart.defaults.font.family = "'Inter', system-ui, sans-serif";

// Model color helpers
function modelColor(modelId, alpha = 1) {
  const rgb = MODELS[modelId].colorRgb;
  return `rgba(${rgb}, ${alpha})`;
}

function modelColors(alpha = 1) {
  return MODEL_ORDER.map(id => modelColor(id, alpha));
}

function modelNames() {
  return MODEL_ORDER.map(id => MODELS[id].name);
}

// Create vertical gradient for bar charts
function createBarGradient(ctx, colorRgb, chartArea) {
  if (!chartArea) return `rgba(${colorRgb}, 0.8)`;
  const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
  gradient.addColorStop(0, `rgba(${colorRgb}, 0.95)`);
  gradient.addColorStop(1, `rgba(${colorRgb}, 0.15)`);
  return gradient;
}

// Create horizontal gradient for horizontal bar charts
function createHBarGradient(ctx, colorRgb, chartArea) {
  if (!chartArea) return `rgba(${colorRgb}, 0.8)`;
  const gradient = ctx.createLinearGradient(chartArea.left, 0, chartArea.right, 0);
  gradient.addColorStop(0, `rgba(${colorRgb}, 0.2)`);
  gradient.addColorStop(1, `rgba(${colorRgb}, 0.95)`);
  return gradient;
}

// Common chart options
const CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  animation: {
    duration: 1000,
    easing: 'easeOutQuart',
  },
  plugins: {
    legend: {
      labels: {
        padding: 16,
        usePointStyle: true,
        pointStyleWidth: 10,
        font: { size: 12 }
      }
    },
    tooltip: {
      backgroundColor: 'rgba(15, 23, 42, 0.95)',
      borderColor: 'rgba(71, 85, 105, 0.4)',
      borderWidth: 1,
      titleFont: { size: 13, weight: '600' },
      bodyFont: { size: 12 },
      padding: { top: 10, bottom: 10, left: 14, right: 14 },
      cornerRadius: 8,
      displayColors: true,
      boxWidth: 8,
      boxHeight: 8,
      boxPadding: 4,
      usePointStyle: true,
    }
  }
};

// Create a grouped bar chart with gradient fills
function createGroupedBarChart(canvasId, labels, datasets, options = {}) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  const chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: datasets.map((ds, i) => {
        const rgb = MODELS[MODEL_ORDER[i]].colorRgb;
        return {
          label: ds.label,
          data: ds.data,
          backgroundColor: function(context) {
            const chart = context.chart;
            const { chartArea } = chart;
            return createBarGradient(chart.ctx, rgb, chartArea);
          },
          borderColor: modelColor(MODEL_ORDER[i], 0.9),
          borderWidth: 1,
          borderRadius: 5,
          borderSkipped: false,
          ...ds,
        };
      })
    },
    options: {
      ...CHART_DEFAULTS,
      animation: {
        ...CHART_DEFAULTS.animation,
        delay: (context) => context.dataIndex * 120 + context.datasetIndex * 250,
      },
      scales: {
        y: {
          beginAtZero: true,
          max: options.maxY || 100,
          ticks: {
            callback: val => val + '%',
            font: { size: 11 }
          },
          grid: { color: 'rgba(51, 65, 85, 0.2)' }
        },
        x: {
          ticks: { font: { size: 11 } },
          grid: { display: false }
        }
      },
      ...options,
    }
  });
  return chart;
}

// Create a horizontal bar chart with gradient fills
function createHorizontalBarChart(canvasId, labels, data, colors, options = {}) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  // Parse colorRgb from hex colors
  function hexToRgb(hex) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `${r}, ${g}, ${b}`;
  }

  const rgbColors = colors.map(c => hexToRgb(c));

  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: function(context) {
          const chart = context.chart;
          const { chartArea } = chart;
          const idx = context.dataIndex;
          return createHBarGradient(chart.ctx, rgbColors[idx], chartArea);
        },
        borderColor: colors.map(c => c),
        borderWidth: 1,
        borderRadius: 5,
        borderSkipped: false,
      }]
    },
    options: {
      ...CHART_DEFAULTS,
      indexAxis: 'y',
      animation: {
        ...CHART_DEFAULTS.animation,
        delay: (context) => context.dataIndex * 200,
      },
      plugins: {
        ...CHART_DEFAULTS.plugins,
        legend: { display: false }
      },
      scales: {
        x: {
          beginAtZero: true,
          ticks: { font: { size: 11 } },
          grid: { color: 'rgba(51, 65, 85, 0.2)' }
        },
        y: {
          ticks: { font: { size: 12, weight: '500' } },
          grid: { display: false }
        }
      },
      ...options,
    }
  });
}

// Create a radar chart
function createRadarChart(canvasId, labels, datasets, options = {}) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  return new Chart(ctx, {
    type: 'radar',
    data: {
      labels: labels,
      datasets: datasets.map((ds, i) => ({
        label: ds.label,
        data: ds.data,
        backgroundColor: modelColor(MODEL_ORDER[i], 0.1),
        borderColor: modelColor(MODEL_ORDER[i], 0.8),
        borderWidth: 2,
        pointBackgroundColor: modelColor(MODEL_ORDER[i], 1),
        pointBorderColor: 'rgba(30, 41, 59, 0.8)',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
        ...ds,
      }))
    },
    options: {
      ...CHART_DEFAULTS,
      scales: {
        r: {
          beginAtZero: true,
          max: 100,
          ticks: {
            stepSize: 20,
            backdropColor: 'transparent',
            font: { size: 10 },
            color: '#475569'
          },
          grid: { color: 'rgba(51, 65, 85, 0.3)' },
          angleLines: { color: 'rgba(51, 65, 85, 0.3)' },
          pointLabels: {
            font: { size: 11, weight: '500' },
            color: '#cbd5e1'
          }
        }
      },
      ...options,
    }
  });
}

// Create a doughnut chart
function createDoughnutChart(canvasId, labels, data, colors, options = {}) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: colors,
        borderColor: 'rgba(30, 41, 59, 0.8)',
        borderWidth: 2,
      }]
    },
    options: {
      ...CHART_DEFAULTS,
      cutout: '60%',
      plugins: {
        ...CHART_DEFAULTS.plugins,
        legend: {
          position: 'bottom',
          labels: {
            padding: 12,
            usePointStyle: true,
            font: { size: 11 }
          }
        }
      },
      ...options,
    }
  });
}

// Create a stacked bar chart with gradient fills
function createStackedBarChart(canvasId, labels, datasets, options = {}) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: datasets.map(ds => ({
        ...ds,
        borderRadius: 2,
        borderWidth: 0,
      })),
    },
    options: {
      ...CHART_DEFAULTS,
      animation: {
        ...CHART_DEFAULTS.animation,
        delay: (context) => context.dataIndex * 150,
      },
      scales: {
        x: {
          stacked: true,
          ticks: { font: { size: 11 } },
          grid: { display: false }
        },
        y: {
          stacked: true,
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: val => val + '%',
            font: { size: 11 }
          },
          grid: { color: 'rgba(51, 65, 85, 0.2)' }
        }
      },
      ...options,
    }
  });
}

// Accuracy color helpers
function accuracyColor(value) {
  if (value >= 0.7) return 'text-emerald-400';
  if (value >= 0.4) return 'text-yellow-400';
  return 'text-red-400';
}

function accuracyBg(value) {
  if (value >= 0.7) return 'bg-emerald-400/10';
  if (value >= 0.4) return 'bg-yellow-400/10';
  return 'bg-red-400/10';
}
