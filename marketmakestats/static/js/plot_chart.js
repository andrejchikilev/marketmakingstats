(function ($){
    $(document).ready(function () {

        function plot_test(){
            var ctx = document.getElementById("myChart");
            ctx.style.height = '400px';
            ctx.style.width = '100%';
            var cfg = {
			type: 'bar',
			data: {
				datasets: [{
					label: 'Market course',
                    data: window.mmslocal.chart_data,
					type: 'line',
					pointRadius: 1,
					fill: false,
					lineTension: 0,
					borderWidth: 2,
                    borderColor: '#33C3F0'
				}]
			},
            options: {
				tooltips: {
					mode: 'index',
					intersect: false,
				},
				hover: {
					mode: 'nearest',
					intersect: true
				},
				scales: {
					xAxes: [{
						type: 'time',
						distribution: 'series',
						ticks: {
							source: 'auto'
						}
					}],
					yAxes: [{
						scaleLabel: {
							display: true,
							labelString: 'Course'
						    }
					    }]
				    }
			    },
		    };
            var myChart = new Chart(ctx, cfg);
        };
        plot_test();
    });
})(jQuery);
