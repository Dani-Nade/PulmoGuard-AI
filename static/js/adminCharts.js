// after you load Chart.js (e.g. at bottom of admindashboard.html)

// 1) Pie: Detection Outcome Distribution
new Chart(document.getElementById('pieChartOutcomes'), {
  type: 'pie',
  data: {
    labels: ['Benign', 'Malignant', 'Uncertain'],
    datasets: [{
      data: [60, 30, 10], // ← replace with real percentages
      backgroundColor: [
        'rgba(54,162,235,0.6)',
        'rgba(255,99,132,0.6)',
        'rgba(255,205,86,0.6)'
      ]
    }]
  },
  options: { responsive: true }
});

// 2) Bar: Scans Per Week
new Chart(document.getElementById('barChartScansPerWeek'), {
  type: 'bar',
  data: {
    labels: ['Week 1','Week 2','Week 3','Week 4','Week 5'],
    datasets: [{
      label: 'Scans',
      data: [12, 18, 15, 22, 19], // ← actual counts
      backgroundColor: 'rgba(75,192,192,0.6)',
      borderColor: 'rgba(75,192,192,1)',
      borderWidth: 1
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: { beginAtZero:true },
      x: { }
    }
  }
});

// 3) Line: User Onboarding Rate
new Chart(document.getElementById('lineChartOnboarding'), {
  type: 'line',
  data: {
    labels: ['Jan','Feb','Mar','Apr','May'], // ← months
    datasets: [{
      label: 'New Users',
      data: [5, 8, 12, 9, 14], // ← actual new‐user counts
      borderColor: 'rgba(153,102,255,1)',
      backgroundColor: 'rgba(153,102,255,0.4)',
      tension: 0.2,
      fill: true
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: { beginAtZero:true }
    }
  }
});

// 4) Histogram: Model Confidence Distribution
new Chart(document.getElementById('histChartConfidenceDist'), {
  type: 'bar',
  data: {
    labels: ['0–20%','21–40%','41–60%','61–80%','81–100%'],
    datasets: [{
      label: 'Count',
      data: [3, 7, 12, 18, 10], // ← bin counts
      backgroundColor: 'rgba(255,159,64,0.6)',
      borderColor: 'rgba(255,159,64,1)',
      borderWidth: 1
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: { beginAtZero:true }
    }
  }
});

// 5) Bar: Top Geographic Regions
new Chart(document.getElementById('barChartRegions'), {
  type: 'bar',
  data: {
    labels: ['Region A','Region B','Region C','Region D'],
    datasets: [{
      label: 'Scans',
      data: [25, 18, 12, 8], // ← actual numbers per region
      backgroundColor: 'rgba(54,162,235,0.6)',
      borderColor: 'rgba(54,162,235,1)',
      borderWidth: 1
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: { beginAtZero:true }
    }
  }
});

// 6) Bar: Error / Manual Review Count
new Chart(document.getElementById('barChartErrorRate'), {
  type: 'bar',
  data: {
    labels: ['Misclassifications','Manual Reviews'],
    datasets: [{
      label: 'Count',
      data: [5, 12], // ← tracked counts
      backgroundColor: ['rgba(255,99,132,0.6)','rgba(255,205,86,0.6)'],
      borderColor: ['rgba(255,99,132,1)','rgba(255,205,86,1)'],
      borderWidth: 1
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: { beginAtZero:true }
    }
  }
});
