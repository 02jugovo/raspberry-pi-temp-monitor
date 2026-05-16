// 存储图表实例，用于更新
let temperatureChartInstance = null;
let predictionChartInstance = null;
let fuzzyChartInstance = null;

// 绘制温度历史图表 - 固定显示最近12小时
function drawTemperatureChart(elementId, data, range = 'hour') {
    const validData = data.filter(item => item.temperature !== null && item.temperature !== undefined);
    if (validData.length === 0) {
        // 显示暂无数据
        const container = document.getElementById(elementId).parentNode;
        container.innerHTML = '<div style="text-align:center;color:#aaa;padding:40px 0;">暂无数据</div>';
        return;
    }
    const sortedData = [...validData].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    let labels;
    let chartTitle = '';
    if (range === 'hour') {
        labels = sortedData.map(item => {
            const date = new Date(item.timestamp);
            return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        });
        chartTitle = '最近12小时温度历史';
    } else if (range === 'day') {
        labels = sortedData.map(item => {
            const date = new Date(item.timestamp);
            return date.getHours() + '时';
        });
        chartTitle = '今日24小时温度';
    } else if (range === 'month') {
        labels = sortedData.map(item => {
            const date = new Date(item.timestamp);
            return (date.getMonth() + 1) + '-' + date.getDate();
        });
        chartTitle = '本月每日温度';
    } else if (range === 'year') {
        labels = sortedData.map(item => {
            const date = new Date(item.timestamp);
            return (date.getMonth() + 1) + '月';
        });
        chartTitle = '本年每月温度';
    } else if (range === 'raw') {
        labels = sortedData.map(item => {
            const date = new Date(item.timestamp);
            return date.toLocaleString();
        });
        chartTitle = '自定义时间段温度曲线';
    } else {
        labels = sortedData.map(item => item.timestamp);
        chartTitle = '温度历史';
    }
    const temperatures = sortedData.map(item => item.temperature);
    const ctx = document.getElementById(elementId).getContext('2d');
    // 独立管理主图表和模糊查询图表实例
    if (elementId === 'temperature-chart') {
        if (temperatureChartInstance) {
            temperatureChartInstance.destroy();
        }
        temperatureChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Temperature (°C)',
                    data: temperatures,
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: chartTitle
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: '温度 (°C)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: (range === 'hour' || range === 'day') ? '时间' : (range === 'month' ? '日期' : (range === 'raw' ? '时间' : '月份'))
                        }
                    }
                }
            }
        });
    } else if (elementId === 'fuzzy-query-chart') {
        if (fuzzyChartInstance) {
            fuzzyChartInstance.destroy();
        }
        fuzzyChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Temperature (°C)',
                    data: temperatures,
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: chartTitle
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: '温度 (°C)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: (range === 'raw' ? '时间' : '时间')
                        }
                    }
                }
            }
        });
    }
}

// 绘制温度预测图表 - 基于表格数据
function drawPredictionChart(elementId, predictionsFromTable) {
    // 过滤无效数据点
    const validData = predictionsFromTable.filter(item => item.temperature !== null && item.temperature !== undefined);
    const ctx = document.getElementById(elementId).getContext('2d');
    if (predictionChartInstance) {
        predictionChartInstance.destroy();
    }
    const labels = validData.map(item => {
        const date = new Date(item.timestamp);
        return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    });
    const temperatures = validData.map(item => item.temperature);
    predictionChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '预测温度 (°C)',
                data: temperatures,
                backgroundColor: 'rgba(255, 159, 64, 0.2)',
                borderColor: 'rgba(255, 159, 64, 1)',
                borderWidth: 2,
                borderDash: [5, 5],
                tension: 0.1,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '温度预测'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: '温度 (°C)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: '时间'
                    }
                }
            }
        }
    });
}
