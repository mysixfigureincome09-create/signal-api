<!DOCTYPE html>
<html>
<head>
    <title>AI Trading Dashboard</title>

    <link rel="stylesheet" href="/static/style.css">

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>

<body>

<div class="header">
    <h1>📊 AI Trading Dashboard</h1>
    <p>Live Buy / Sell / Hold Signals</p>
</div>

<div class="grid">

{% for s in stocks %}

<div class="card {{ s.signal }}">

    <div class="top">
        <h2>{{ s.ticker }}</h2>
        <span class="badge {{ s.signal }}">{{ s.signal }}</span>
    </div>

    <div class="price">
        ${{ "%.2f"|format(s.price) }}
    </div>

    <div class="score">
        Score: {{ s.score }}
    </div>

    <canvas id="chart{{ loop.index }}"></canvas>

</div>

<script>
const ctx{{ loop.index }} = document.getElementById('chart{{ loop.index }}');

new Chart(ctx{{ loop.index }}, {
    type: 'line',
    data: {
        labels: [1,2,3,4,5],
        datasets: [{
            data: [
                {{ s.price * 0.98 }},
                {{ s.price * 0.99 }},
                {{ s.price }},
                {{ s.price * 1.01 }},
                {{ s.price * 1.02 }}
            ],
            borderColor: "#00ffcc",
            borderWidth: 2,
            pointRadius: 0
        }]
    },
    options: {
        responsive: true,
        plugins: { legend: { display: false }},
        scales: { x: { display: false }, y: { display: false } }
    }
});
</script>

{% endfor %}

</div>

</body>
</html>
