(function () {
    var interval,
        update_chart;
    var config = window.twitter_stream_status_data;

    var UPDATE_INTERVAL = 15000;
    var CHART_HEIGHT = 250;

    function chart(target_element, config) {


        var margin = {top: 5, right: 20, bottom: 30, left: 50},
            width = config.width - margin.left - margin.right,
            height = config.height - margin.top - margin.bottom;

        var x = d3.time.scale()
            .range([0, width]);

        var y = d3.scale.linear()
            .range([height, 0])
            .domain([0, 1]);

        var xAxis = d3.svg.axis()
            .scale(x)
            .orient("bottom");

        var yAxis = d3.svg.axis()
            .scale(y)
            .orient("left");

        var svg = d3.select(target_element).append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        var xAxisGroup = svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")");

        var yAxisGroup = svg.append("g")
            .attr("class", "y axis");

        yAxisGroup.append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", 6)
            .attr("dy", ".71em")
            .style("text-anchor", "end")
            .text("Tweets");

        var barsGroup = svg.append("g")
            .attr('class', 'bars');

        return function (data) {

            data.forEach(function (d) {
                d.time = new Date(d.time);
            });

            var dateRange = d3.extent(data, function (d) {
                return d.time;
            });

            var now = new Date();
            now.setSeconds(0);
            now.setMilliseconds(0);
            x.domain([dateRange[0], Math.max(now, dateRange[1])]);

            y.domain([0, d3.max(data, function (d) {
                return d.tweets;
            })]);

            var leftMargin = 22;
            var minutesShown = (now - dateRange[0]) / 60000;
            var barWidth = Math.floor((width - leftMargin) / minutesShown);
            barWidth = Math.max(1, barWidth - (barWidth % 20));

            x.range([barWidth / 2 + leftMargin, width]);

            xAxisGroup.call(xAxis);
            yAxisGroup.call(yAxis);

            var bind = barsGroup.selectAll("g")
                .data(data);

            var enter = bind.enter()
                .append('g');
            enter.append('rect')
            enter.append('text')
                .attr("dy", ".75em");

            bind.exit()
                .remove();

            bind.attr('transform', function (d, i) {
                return "translate(" + (x(d.time) - barWidth / 2) + ",0)";
            })
                .classed('filling', function (d, i) {
                    return i == data.length - 1
                });

            bind.select('rect')
                .attr('width', barWidth - 1)
                .transition()
                .attr("y", function (d) {
                    return y(d.tweets);
                })
                .attr('height', function (d) {
                    return height - y(d.tweets);
                });

            bind.select('text')
                .attr("x", barWidth / 2)
                .text(function (d) {
                    return d.tweets;
                })
                .transition()
                .attr("y", function (d) {
                    return y(d.tweets) + 3;
                });
        };
    }


    function update() {
        toggle_status_label(false);
        $.get(config.update_url)
            .done(function (response) {
                status_display.html(response.display);
                update_chart(response.timeline);
                toggle_status_label(true);
            })
            .fail(function (err, xhr) {
                console.log(err, xhr);
            });
    }

    function toggle_status_label(show) {
        var label = $('.status-label');
        label[0].borderWidth;

        if (show) {
            label.addClass('in');
        } else {
            label.removeClass('in');
        }
    }

    $(document).ready(function () {
        status_display = $('#twitter-stream-display');

        var chart_element = $('#twitter-stream-chart');
        update_chart = chart(chart_element[0], {
            width: chart_element.width(),
            height: CHART_HEIGHT
        });
        update_chart(config.timeline_data);
        interval = setInterval(update, UPDATE_INTERVAL);
        toggle_status_label(true);
    });
})();