// 1) Scan History Over Time (Line)
new Chart(document.getElementById("lineChartHistory"), {
  type: "line",
  data: {
    labels: ["2025-01-01","2025-02-15","2025-03-20","2025-04-10","2025-05-01"],
    datasets: [{
      label: "Health Score",
      data:    [2.5,         3.0,         2.8,         3.2,         3.1],
      borderColor: "rgba(54,162,235,0.8)",
      backgroundColor: "rgba(54,162,235,0.4)",
      tension: 0.2,
      fill: true
    }]
  },
  options: {
    responsive: true,
    scales: {
      x: { grid: { color: "rgba(255,255,255,0.2)" } },
      y: { beginAtZero:true, grid: { color: "rgba(255,255,255,0.2)" } }
    }
  }
});

// 2) Prediction Confidence per Scan (Bar)
new Chart(document.getElementById("barChartConfidence"), {
  type: "bar",
  data: {
    labels: ["Scan 1","Scan 2","Scan 3","Scan 4","Scan 5"],
    datasets:[{
      label: "Confidence (%)",
      data:    [70,       85,       60,       90,       75],
      backgroundColor: "rgba(255,159,64,0.6)",
      borderColor:     "rgba(255,159,64,1)",
      borderWidth: 1
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: { beginAtZero:true, max:100, grid:{color:"rgba(255,255,255,0.2)"} },
      x: { grid:{color:"rgba(255,255,255,0.2)"} }
    }
  }
});

// 3) Lung Health Score Trend (Radar)
new Chart(document.getElementById("radarChartHealthTrend"), {
  type: "radar",
  data: {
    labels: ["Upper Left","Upper Right","Lower Left","Lower Right","Central"],
    datasets:[{
      label: "Score",
      data:    [3.0,         2.8,         3.2,         2.9,         3.1],
      backgroundColor: "rgba(153,102,255,0.4)",
      borderColor:     "rgba(153,102,255,1)",
      borderWidth: 1
    }]
  },
  options: {
    responsive: true,
    scale: {
      ticks: { beginAtZero:true },
      grid:  { color:"rgba(255,255,255,0.2)" }
    }
  }
});

// 4) Comparative Risk Benchmark (Bar)
new Chart(document.getElementById("barChartBenchmark"), {
  type: "bar",
  data: {
    labels: ["You","Population Avg"],
    datasets:[{
      label: "Risk Score",
      data:    [3.2,   2.5],
      backgroundColor: ["rgba(75,192,192,0.6)","rgba(255,99,132,0.6)"],
      borderColor:     ["rgba(75,192,192,1)","rgba(255,99,132,1)"],
      borderWidth: 1
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: { beginAtZero:true, grid:{color:"rgba(255,255,255,0.2)"} },
      x: { grid:{color:"rgba(255,255,255,0.2)"} }
    }
  }
});

// 5) Scan Result Types Breakdown (Doughnut)
new Chart(document.getElementById("doughnutChartResults"), {
  type: "doughnut",
  data: {
    labels: ["Benign","Malignant","Inconclusive"],
    datasets:[{
      data:    [60,       30,           10],
      backgroundColor:[
        "rgba(54,162,235,0.6)",
        "rgba(255,99,132,0.6)",
        "rgba(255,205,86,0.6)"
      ]
    }]
  },
  options: { responsive:true }
});

// 6) Time Between Scans (Histogram as Bar)
new Chart(document.getElementById("histogramChartTimeBetweenScans"), {
  type: "bar",
  data: {
    labels: ["0–30 days","31–60 days","61–90 days","91–120 days"],
    datasets:[{
      label: "Count of Scans",
      data:    [2,          3,           1,            1],
      backgroundColor: "rgba(255,159,64,0.6)",
      borderColor:     "rgba(255,159,64,1)",
      borderWidth: 1
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: { beginAtZero:true, grid:{color:"rgba(255,255,255,0.2)"} },
      x: { grid:{color:"rgba(255,255,255,0.2)"} }
    }
  }
});
