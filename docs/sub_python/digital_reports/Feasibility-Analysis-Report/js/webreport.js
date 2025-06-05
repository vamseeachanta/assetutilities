$(document).ready(function(){
    
    //Sidebar function
    
    $(document).scroll(function(){
         
        var offsetPixel = 23;
        
        if($(window).width() > 768) {
            
            if($(window).scrollTop() > offsetPixel) {
             
                $('#sidebar').css('position', 'fixed');
                $('#sidebar').css('top', 0);
                $('#sidebar').css('width', '21%');
                
            } else { 
             
                $('#sidebar').css('position', 'static');
                $('#sidebar').css('top', 0);
                $('#sidebar').css('width', '100%');

            }
            
        }
         
    }); 
    
    //Heading function
    $("#head").sticky({topSpacing:0});
    $("#head2").sticky({topSpacing:0});
    $("#head3").sticky({topSpacing:0});
    $("#head4").sticky({topSpacing:0});
    $("#head5").sticky({topSpacing:0});
    $("#head6").sticky({topSpacing:0});
    
    //Image animation library
    $('.img-popup').magnificPopup({
        
        type: 'image'
        
    });
    
    //CSV to Table init
    
    csvToTable();
    
    //Initialize charts here
    
    mooringVesselPosition1();
    mooringVesselPosition2();

    lowestTensionMooring8();
    highestTensionMooring8();
    lowestTensionMooring12();
    highestTensionMooring12();

    strokeRiser1();
    strokeRiser2();

    strokeVsOffset();

    riserStrokeVesselPosition();

    riserStressSlackResponses();
    riserStressStretchResponses();
    riserStressResponseRiserSlack();

    stressResponseRiserStretch();
    
    
});

function scrollToDiv(div) {
    
    $('html, body').animate({
		scrollTop: $(div).offset().top
	},1000);
    
}

//CSV to Table

function csvToTable() {
    
    d3.text('csv/VesselPosition_8Point.csv', function(data){
        
        var parsedCSV = d3.csv.parseRows(data);
        
        var container = d3.select('#table')
            .append("table")
        
            .selectAll("tr")
                .data(parsedCSV).enter()
                .append("tr")
        
            .selectAll("td")
                .data(function(d){return d;}).enter()
                .append("td")
                .text(function(d){return d;});
        
    });
    
}

//Google charts

google.charts.load('current',{packages:['corechart', 'controls']});
google.charts.setOnLoadCallback(effectiveTensionRiserLength);
google.charts.setOnLoadCallback(effectiveTensionRiserLength2);
google.charts.setOnLoadCallback(lateralDisplacementAlongLength);
google.charts.setOnLoadCallback(stressAlongLength);
google.charts.setOnLoadCallback(stressAlongLength2);

//Google Charts Goes Here

function stressAlongLength2 () {
    
    $.getScript('js/jquery-csv.js', function(){
        
        $.get('csv/6/Stress (ksi) along the Length of the Riser during Strech.csv', function (csvData){
            
            var arrayData = $.csv.toArrays(csvData,
                                           {onParseValue: $.csv.hooks.castToScalar}),
                data = new google.visualization.arrayToDataTable(arrayData),
                options = {
                    
                    title: 'Effective Tension (kN) along with Riser Length',
                    hAxis: {
                        title: 'Riser length (ft)',
                        format: 'decimal'
                    },
                    vAxis: {
                        title: 'VM Stress (ksi)'
                    },
                    height: 500,
                    width: 800,
                    pointsVisible: true
                    
                };
                
            chart = new google.visualization
                        .LineChart(document.getElementById('gchart4'));
            chart.draw(data, options); 
            
        }, 'text');
        
    });
    
}

function stressAlongLength() {
    
    $.getScript('js/jquery-csv.js', function(){
        
        $.get('csv/6/Stress (ksi) along the Length of the Riser during Strech(Top 100ft).csv', function (csvData){
            
            var arrayData = $.csv.toArrays(csvData,
                                           {onParseValue: $.csv.hooks.castToScalar}),
                data = new google.visualization.arrayToDataTable(arrayData),
                options = {
                    
                    title: 'Effective Tension (kN) along with Riser Length',
                    hAxis: {
                        title: 'Riser length (ft)'
                    },
                    vAxis: {
                        title: 'VM Stress (ksi)'
                    },
                    height: 500,
                    width: 800,
                    pointsVisible: true
                    
                };
                
            chart = new google.visualization
                        .LineChart(document.getElementById('gchart5'));
            chart.draw(data, options); 
            
        }, 'text');
        
    });
    
}

function lateralDisplacementAlongLength () {
    
    $.getScript('js/jquery-csv.js', function(){
        
        $.get('csv/6/Lateral Displacement Along the Length of Riser during Stretch.csv', function (csvData){
            
            var arrayData = $.csv.toArrays(csvData,
                                           {onParseValue: $.csv.hooks.castToScalar}),
                data = new google.visualization.arrayToDataTable(arrayData),
                options = {
                    
                    title: 'Effective Tension (kN) along with Riser Length',
                    hAxis: {
                        title: 'Riser length (ft)'
                    },
                    vAxis: {
                        title: 'Lateral Displacement (ft)'
                    },
                    height: 500,
                    width: 800,
                    
                };
                
            chart = new google.visualization
                        .LineChart(document.getElementById('gchart3'));
            chart.draw(data, options); 
            
        }, 'text');
        
    });
    
}

function effectiveTensionRiserLength () {
    
    $.getScript('js/jquery-csv.js', function(){
        
        $.get('csv/6/Effective Tension Along the Riser length(Top 100ft).csv', function (csvData){
            
            var arrayData = $.csv.toArrays(csvData,
                                           {onParseValue: $.csv.hooks.castToScalar}),
                data = new google.visualization.arrayToDataTable(arrayData),
                options = {
                    
                    title: 'Effective Tension (kN) along with Riser Length',
                    hAxis: {
                        title: 'Riser length (ft)'
                    },
                    vAxis: {
                        title: 'Effective Tension (kips)'
                    },
                    height: 500,
                    width: 800,
                    pointsVisible: true
                    
                };
                
            chart = new google.visualization
                        .LineChart(document.getElementById('gchart2'));
            chart.draw(data, options); 
            
        }, 'text');
        
    });
    
}

function effectiveTensionRiserLength2 () {
    
    $.getScript('js/jquery-csv.js',  function(){
        
        $.get('csv/6/Effective Tension Along the Riser length.csv', function(csvData){

            var arrayData = $.csv.toArrays(csvData,
                                      {onParseValue: $.csv.hooks.castToScalar}),
            data = new google.visualization.arrayToDataTable(arrayData),
            options = {
                
                title: 'Effective Tension (kN) along with Riser Length',
                hAxis: {
                    title: 'Riser length (ft)'
                },
                vAxis: {
                    title: 'Effective Tension (kips)'
                },
                height: 500,
                width: 800,
            };

            chart  = new google.visualization
                        .LineChart(document.getElementById('gchart'));
            chart.draw(data, options);

        }, 'text');
        
    });

    //Getting the CSV

}

//functions for each individual NVD3 graph goes here

function mooringVesselPosition1 () {
    
    var scatterData = [];
    
    d3.csv('csv/VesselPosition_8Point.csv', function(error, data) {
        
        var scatterPoints = [];
        
        var static = [];
        var wind = [];
        var current = [];
        var hurricane = [];
        
        data.forEach(function(d){
            
            d.Surge = d.Surge;
            d.Sway = +d.Sway;
            
            scatterPoints.push({x: d.Surge, y: d.Sway});
            
        });
        
        static = [{x: scatterPoints[0].x, y: scatterPoints[0].y}];
        
        wind = [{x: scatterPoints[1].x, y: scatterPoints[1].y}];
        
        current = [{x: scatterPoints[2].x, y: scatterPoints[2].y}];
        
        hurricane = [{x: scatterPoints[3].x, y: scatterPoints[3].y}];
        
        scatterData = [
            
            {
                
                key: 'Static',
                values: static
                
            },{
                
                key: 'Wind',
                values: wind
                
            },{
                
                key: 'Current',
                values: current
                
            },{
                
                key: '100 yr Hurricane',
                values: hurricane
                
            }
            
        ];
        
        console.log(scatterData);
        
        nv.addGraph(function() {
            
            var chart = nv.models.scatterChart()
                                .showDistX(true)
                                .showDistY(true);
            
            chart.color(['#2F4FF6']);
            
            chart.pointRange([100, 100]);
            
            chart.pointShape('square');
            
            chart.height(500);
            
            chart.xAxis
                .axisLabel('Surge (m)')
                .tickFormat(d3.format(',.1f'));
            
            chart.forceX([-10,100]);
            
            chart.yAxis
                .axisLabel('Sway (m)')
                .tickFormat(d3.format(',.1f'));
            
            chart.forceY([-10, 100]);
            
            d3.select('#chart1 svg') 
                .datum(scatterData)
                .call(chart);
        
            nv.utils.windowResize(function() { chart.update() }); 
        
            return chart;
            
        });
        
    });
    
}

function mooringVesselPosition2() {
    
    var scatterData = [];
    
    d3.csv('csv/VesselPosition_12Point.csv', function(error, data) {
        
        var scatterPoints = [];
        
        var static = [];
        var wind = [];
        var current = [];
        var hurricane = [];
        
        data.forEach(function(d){
            
            d.Surge = +d.Surge;
            d.Sway = +d.Sway;
            
            scatterPoints.push({x: d.Surge, y: d.Sway});
            
        });
        
        static = [scatterPoints[0]];
        
        wind = [scatterPoints[1]];
        
        current = [scatterPoints[2]];
        
        hurricane = [scatterPoints[3]];
        
        scatterData = [
            
            {
                
                key: 'Static',
                values: static
                
            },{
                
                key: 'Wind',
                values: wind
                
            },{
                
                key: 'Current',
                values: current
                
            },{
                
                key: '100 yr Hurricane',
                values: hurricane
                
            }
            
        ];
        
        nv.addGraph(function() {
            
            var chart = nv.models.scatterChart()
                                .showDistX(true)
                                .showDistY(true)
                                .interactive(true)
                                .useVoronoi(true);
            
            chart.pointRange([100, 100]);
            
            chart.pointShape('square');
            
            chart.color(['#2F4FF6']);
            
            chart.height(500);
            
            chart.xAxis
                .axisLabel('Surge (m)')
                .tickFormat(d3.format(',.1f'));
            
            chart.forceX([-10,60]);
            
            chart.yAxis
                .axisLabel('Sway (m)')
                .tickFormat(d3.format(',.1f'));
            
            chart.forceY([-10, 60]);
            
            d3.select('#chart2 svg') 
                .datum(scatterData)
                .call(chart);
        
            nv.utils.windowResize(function() { chart.update() }); 
        
            return chart;
            
        });
        
    });
    
}

function lowestTensionMooring8() {
    
    //Initializing object array to keep csv data
    var lineData = [];
    
    //Get CSV file
    d3.csv('csv/8P_ET along high Tension Line1.csv', function (error, data){
        
        //Array objects to keep data for each line
        var static = [];
        var wind = [];
        var current = [];
        var all = [];
        
        //This method goes through each row in the CSV file
        data.forEach(function (d) {
            
            //These turn strings into integers
            d.MooringLineLength = +d.MooringLineLength;
            d.Static = +d.Static;
            d.Wind = +d.Wind;
            d.Current = +d.Current;
            d.All = +d.All;
            
            //This method pushes each value into their array objects above
            //The array objects must have an x and y point like below, as it is required in a line graph
            static.push({x:d.MooringLineLength, y:d.Static});
            wind.push({x:d.MooringLineLength, y:d.Wind});
            current.push({x:d.MooringLineLength, y:d.Current});
            all.push({x:d.MooringLineLength, y:d.All});
            
        });
        
        //This is the array object that is passed to the graph as data to plot
        lineData = [
            
            {
                
                key: 'Static', //The name for the line
                values: static, //The array object that we initialized before that contains the points (x, y)
                color: '#2F4FF6' //color of the line
                
            },{
                
                key: 'Wind',
                values: wind,
                color: '#1C7F11'
                
            },{
                
                key: 'Current',
                values: current,
                color: '#F6281E'
                
            },{
                
                key: 'All',
                values: all,
                color: '#0FE5FF'
                
            }
            
        ];
        
        nv.addGraph(function(){ //This is where we declare the graph
        
            var chart = nv.models.lineWithFocusChart()
                            .useInteractiveGuideline(true) //Self explanatory 
                            .showYAxis(true)
                            .showXAxis(true);
            
            chart.height(500); //Height of the graph in px
        
            chart.xAxis
                .axisLabel('Mooring Line Length (m)') // Labelling the x axis
                .tickFormat(d3.format(',.1f')); //To 1 decimal place
        
            chart.forceX([0,1500]); //This forces the graph to have a minimum point of 0 and a maximum point of 3250
            
            chart.yAxis
                .axisLabel('Effective Tension (mT)')
                .tickFormat(d3.format(',.1f'));
            
            chart.forceY([0,100,200,300,400,500,600,700,800]);
        
            d3.select('#chart3 svg') //This is where the graph will be placed
                .datum(lineData) //Passing in the graph data
                .call(chart); //calling the chart
        
            nv.utils.windowResize(function() { chart.update() }); //This reformats the graph after the user window has been resized
        
            return chart; //This basically calls the chart into the website
        
        });
        
    });
    
}

function highestTensionMooring8() {
    
    var lineData = [];
    
    d3.csv('csv/8P_ET along high Tension Line6.csv', function (error, data) {
        
        var static = [];
        var wind = [];
        var current = [];
        var all = [];
        
        data.forEach(function (d) {
            
            d.MooringLineLength = +d.MooringLineLength;
            d.Static = +d.Static;
            d.Wind = +d.Wind;
            d.Current = +d.Current;
            d.All = +d.All;
        
            static.push({x:d.MooringLineLength, y:d.Static});
            wind.push({x:d.MooringLineLength, y:d.Wind});
            current.push({x:d.MooringLineLength, y:d.Current});
            all.push({x:d.MooringLineLength, y:d.All});
            
        });
        
            
        lineData = [

            {

                key: 'Static',
                values: static,
                color: '#2F4FF6'

            }, {
                
                key: 'Wind',
                values: wind,
                color: '#1C7F11'
                
            }, {
                
                key: 'Current',
                values: current,
                color: '#F6281E'
                
            }, {
                
                key: 'All',
                values: all,
                color: '#0FE5FF'
                
            }

        ];
        
        nv.addGraph(function(){ 
        
            var chart = nv.models.lineWithFocusChart()
                            .useInteractiveGuideline(true)  
                            .showYAxis(true)
                            .showXAxis(true);
            
            chart.height(500);
        
            chart.xAxis
                .axisLabel('Mooring Line Length (m)')
                .tickFormat(d3.format(',.1f'));
        
            chart.forceX([0,3250]);
            
            chart.yAxis
                .axisLabel('Effective Tension (mT)')
                .tickFormat(d3.format(',.1f'));
            
            chart.forceY([0, 1200]);
        
            d3.select('#chart4 svg') 
                .datum(lineData)
                .call(chart);
        
            nv.utils.windowResize(function() { chart.update() }); 
        
            return chart;
        
        });
        
    });
    
}

function lowestTensionMooring12() {
    
    var lineData = [];
    
    d3.csv('csv/12P_ET along high Tension Line1.csv', function (error, data) {
        
        var static = [];
        var wind = [];
        var current = [];
        var all = [];
        
        data.forEach(function (d) {
            
            d.MooringLineLength = +d.MooringLineLength;
            d.Static = +d.Static;
            d.Wind = +d.Wind;
            d.Current = +d.Current;
            d.All = +d.All;
        
            static.push({x:d.MooringLineLength, y:d.Static});
            wind.push({x:d.MooringLineLength, y:d.Wind});
            current.push({x:d.MooringLineLength, y:d.Current});
            all.push({x:d.MooringLineLength, y:d.All});
            
        });
        
            
        lineData = [

            {

                key: 'Static',
                values: static,
                color: '#2F4FF6'

            }, {
                
                key: 'Wind',
                values: wind,
                color: '#1C7F11'
                
            }, {
                
                key: 'Current',
                values: current,
                color: '#F6281E'
                
            }, {
                
                key: 'All',
                values: all,
                color: '#0FE5FF'
                
            }

        ];
        
        nv.addGraph(function(){ 
        
            var chart = nv.models.lineWithFocusChart()
                            .useInteractiveGuideline(true)  
                            .showYAxis(true)
                            .showXAxis(true);
            
            chart.height(500);
        
            chart.xAxis
                .axisLabel('Mooring Line Length (m)')
                .tickFormat(d3.format(',.1f'));
        
            chart.forceX([0,3250]);
            
            chart.yAxis
                .axisLabel('Effective Tension (mT)')
                .tickFormat(d3.format(',.1f'));
            
            chart.forceY([0, 800]);
        
            d3.select('#chart5 svg') 
                .datum(lineData)
                .call(chart);
        
            nv.utils.windowResize(function() { chart.update() }); 
        
            return chart;
        
        });
        
    });
    
}

function highestTensionMooring12() {
    
    d3.csv('csv/12P_ET along high Tension Line8.csv', function(error, data){
        
        var static = [];
        var wind = [];
        var current = [];
        var all = [];
        
        data.forEach(function (d) {
            
            d.MooringLineLength = +d.MooringLineLength;
            d.Static = +d.Static;
            d.Wind = +d.Wind;
            d.Current = +d.Current;
            d.All = +d.All;
        
            static.push({x:d.MooringLineLength, y:d.Static});
            wind.push({x:d.MooringLineLength, y:d.Wind});
            current.push({x:d.MooringLineLength, y:d.Current});
            all.push({x:d.MooringLineLength, y:d.All});
            
        });
        
            
        lineData = [

            {

                key: 'Static',
                values: static,
                color: '#2F4FF6'

            }, {
                
                key: 'Wind',
                values: wind,
                color: '#1C7F11'
                
            }, {
                
                key: 'Current',
                values: current,
                color: '#F6281E'
                
            }, {
                
                key: 'All',
                values: all,
                color: '#0FE5FF'
                
            }

        ];
        
        nv.addGraph(function(){ 
        
            var chart = nv.models.lineWithFocusChart()
                            .useInteractiveGuideline(true)  
                            .showYAxis(true)
                            .showXAxis(true);
            
            chart.height(500);
        
            chart.xAxis
                .axisLabel('Mooring Line Length (m)')
                .tickFormat(d3.format(',.1f'));
        
            chart.forceX([0,3250]);
            
            chart.yAxis
                .axisLabel('Effective Tension (mT)')
                .tickFormat(d3.format(',.1f'));
            
            chart.forceY([0, 1200]);
        
            d3.select('#chart6 svg') 
                .datum(lineData)
                .call(chart);
        
            nv.utils.windowResize(function() { chart.update() }); 
        
            return chart;
        
        });
        
    });
    
}

function strokeRiser1() {
    
    var lineData = [];
    
    d3.csv('csv/Riser Stretch & Tensioner stroke.csv', function(error, data){
        
        var tensionStroke = [];
        var vesselHeave = [];
        var riserStretch = [];
        
        data.forEach(function (d){
            
            d.Time = +d.Time;
            d.TensionStroke = +d.TensionStroke;
            d.VesselHeave = +d.VesselHeave;
            d.RiserStretch = +d.RiserStretch;
            
            tensionStroke.push({x:d.Time, y:d.TensionStroke});
            vesselHeave.push({x:d.Time, y:d.VesselHeave});
            riserStretch.push({x:d.Time, y:d.RiserStretch});
            
        });
        
        lineData = [
            
            {
                
                key: 'Tension Stroke',
                values: tensionStroke,
                color: '#2F4FF6'
                
            },{
                
                key: 'Vessel Heave',
                values: vesselHeave,
                color: '#1C7F11'
                
            },{
                
                key: 'Riser Stretch',
                values: riserStretch,
                color: '#F6281E'
                
            }
            
        ];
        
         nv.addGraph(function(){ 
        
            var chart = nv.models.lineWithFocusChart()
                            .useInteractiveGuideline(true)  
                            .showYAxis(true)
                            .showXAxis(true);
            
            chart.height(500);
        
            chart.xAxis
                .axisLabel('Time (s)')
                .tickFormat(d3.format(',.1f'));
        
            chart.forceX([100,200]);
            
            chart.yAxis
                .axisLabel('Distance (m)')
                .tickFormat(d3.format(',.1f'));
            
            chart.forceY([-10, 70]);
        
            d3.select('#chart7 svg') 
                .datum(lineData)
                .call(chart);
        
            nv.utils.windowResize(function() { chart.update() }); 
        
            return chart;
        
        });
        
    });
    
}

function strokeRiser2() {
    
    var lineData = [];
    
    d3.csv('csv/RiserSlackTensionStroke.csv', function(error, data){
        
        var tensionStroke = [];
        var vesselHeave = [];
        var riserSlack = [];
        
        data.forEach(function(d){
            
            d.Time = +d.Time;
            d.TensionStroke = +d.TensionStroke;
            d.VesselHeave = +d.VesselHeave;
            d.RiserSlack = +d.RiserSlack;
            
            tensionStroke.push({x:d.Time, y:d.TensionStroke});
            vesselHeave.push({x:d.Time, y:d.VesselHeave});
            riserSlack.push({x:d.Time, y:d.RiserSlack});
            
        });
        
        lineData = [
            
            {
                
                key: 'Tension Stroke',
                values: tensionStroke,
                color:'#2F4FF6'
                
            },{
                
                key: 'Vessel Heave',
                values: vesselHeave,
                color: '#1C7F11'
                
            },{
                
                key: 'Riser Slack',
                values: riserSlack,
                color: '#F6281E',
                
            }
            
        ];
        
        nv.addGraph(function(){ 
        
            var chart = nv.models.lineWithFocusChart()
                            .useInteractiveGuideline(true)  
                            .showYAxis(true)
                            .showXAxis(true);
            
            chart.height(500);
        
            chart.xAxis
                .axisLabel('Time (s)')
                .tickFormat(d3.format(',.1f'));
        
            chart.forceX([100,200]);
            
            chart.yAxis
                .axisLabel('Distance (m)')
                .tickFormat(d3.format(',.1f'));
            
            chart.forceY([-80, 20]);
        
            d3.select('#chart8 svg') 
                .datum(lineData)
                .call(chart);
        
            nv.utils.windowResize(function() { chart.update() }); 
        
            return chart;
        
        });
        
    });
    
}

function strokeVsOffset() {
    
    var lineData = [];
    
    d3.csv('csv/Stroke vs Offset.csv', function(error, data){
        
        var stroke = [];
        var dottedLine = [{x: 6, y:-22},{x: 6, y:-20},{x: 6, y:-18},{x: 6, y:-16},{x: 6, y:-14},{x: 6, y:-12},{x: 6, y:-10},{x: 6, y:-8},{x: 6, y:-6},{x: 6, y:-4},{x: 6, y:-2},{x: 6, y:-0}];
        
        data.forEach(function(d){
            
            d.Offset = +d.Offset;
            d.Stroke = +d.Stroke;
            
            stroke.push({x: d.Offset, y:d.Stroke});
            
        });
        
        lineData = [
            
            {
                
                key: 'Stroke',
                values: stroke,
                color: '#2F4FF6'
                
            },{
                
                key: 'Max expected offset for all conditions',
                values: dottedLine,
                color: '#F6281E',
                classed: 'dashed',
                
            }
            
        ];
        
        nv.addGraph(function(){ 
        
            var chart = nv.models.lineWithFocusChart()
                            .useInteractiveGuideline(true)  
                            .showYAxis(true)
                            .showXAxis(true);
            
            chart.height(500);
        
            chart.xAxis
                .axisLabel('Offset (%)')
                .tickFormat(d3.format(',.1f'));
        
            chart.forceX([-2,10]);
            
            chart.yAxis
                .axisLabel('Stroke (ft)')
            .tickFormat(d3.format(',.1f'));
            
            chart.forceY([-22, 0]);
        
            d3.select('#chart9 svg') 
                .datum(lineData)
                .call(chart);
        
            nv.utils.windowResize(function() { chart.update() }); 
        
            return chart;
        
        });
        
    });
    
}

function riserStrokeVesselPosition () {
    
    var lineBarData = [];
    
    //manually adding data
    
    lineBarData = [
        
      {
      
          key: 'Wave/Wind - Min Vassel Position',
          values: [
              
              {x: 'Offset', y: 0},
              {x: 'Offset & Current', y: 0},
              {x: 'Offset, Current and Wave', y: 19.4},
              {x: 'Offset, Curren, Wave and Low Tide', y: 19.4},
              {x: '1 Riser Connected, Mean Tide', y:17.1},
              {x: '2 Risers Connected, Mean Tide', y:15.5}
          
          ]
      
      },{
          
          key: 'Storm Surge (Downstroke)',
          values: [
              
              {x: 'Offset', y: 0},
              {x: 'Offset & Current', y: 0},
              {x: 'Offset, Current and Wave', y: -3},
              {x: 'Offset, Curren, Wave and Low Tide', y: -3},
              {x: '1 Riser Connected, Mean Tide', y: -3},
              {x: '2 Risers Connected, Mean Tide', y: -3}
          
          ]
          
      },{
          
          key: 'Current (Downstroke)',
          values: [
              
              {x: 'Offset', y: 0},
              {x: 'Offset & Current', y: -1},
              {x: 'Offset, Current and Wave', y: -1},
              {x: 'Offset, Curren, Wave and Low Tide', y: -1},
              {x: '1 Riser Connected, Mean Tide', y: -1},
              {x: '2 Risers Connected, Mean Tide', y: -1}
          
          ]
          
      },{
          
          key: 'Offset (Downstroke)',
          values: [
              
              {x: 'Offset', y: -5},
              {x: 'Offset & Current', y: -5},
              {x: 'Offset, Current and Wave', y: -5},
              {x: 'Offset, Curren, Wave and Low Tide', y: -5},
              {x: '1 Riser Connected, Mean Tide', y: -5},
              {x: '2 Risers Connected, Mean Tide', y: -5}
          
          ]
          
      },{
          
          key: 'Wave/Wind - Max Vassel Position',
          values: [
              
              {x: 'Offset', y: 0},
              {x: 'Offset & Current', y: 0},
              {x: 'Offset, Current and Wave', y: -26.5},
              {x: 'Offset, Curren, Wave and Low Tide', y: -26.5},
              {x: '1 Riser Connected, Mean Tide', y: -24.9},
              {x: '2 Risers Connected, Mean Tide', y: -23.9}
          
          ]
          
      },{
          
          key: 'Riser Slack',
          values: [
              
              {x: 1, y: 0},
              {x: 2, y: 0},
              {x: 3, y: 19.4},
              {x: 4, y: 19.4},
              {x: 5, y:17.1},
              {x: 6, y:15.5}
              
          ]
          
      },{
          
          key: 'Riser Stretch',
          values: [
              
              {x: 1, y: -5},
              {x: 2, y: -6},
              {x: 3, y: -35.4},
              {x: 4, y: -35.4},
              {x: 5, y: -33.9},
              {x: 6, y: -32.8}
              
          ]
          
      },{
          
          key: 'Tensioner Mean Position',
          values: [
              
              {x: 1, y: -5},
              {x: 2, y: -6},
              {x: 3, y: -9},
              {x: 4, y: -9},
              {x: 5, y: -9},
              {x: 6, y: -9}
              
          ]
          
      }
        
    ];
    
    lineBarData[0].type = "bar";
    lineBarData[0].yAxis = 1;
    lineBarData[1].type = "bar";
    lineBarData[1].yAxis = 1;
    lineBarData[2].type = "bar";
    lineBarData[2].yAxis = 1;
    lineBarData[3].type = "bar";
    lineBarData[3].yAxis = 1;
    lineBarData[4].type = "bar";
    lineBarData[4].yAxis = 1;
    lineBarData[5].type = "line";
    lineBarData[5].yAxis = 1;
    lineBarData[6].type = "line";
    lineBarData[6].yAxis = 1;
    lineBarData[7].type = "line";
    lineBarData[7].yAxis = 1;
    
    
    nv.addGraph(function(){ 
        
        
        var chart = nv.models.multiChart()
                        .color(["#E0F2F1","#80CBC4","#26A69A","00897B","#00695C", "#FF5722", "#F44336", "#FF9800"]);
        
        chart.bars1.stacked(true);
        
        chart.height(500);
        
        d3.select('#chart10 svg') 
            .datum(lineBarData)
            .call(chart);
        
        return chart;
        
    });
    
}

function riserStressSlackResponses (){
    
    lineDatas = [];
    
    d3.csv('csv/5.3/Riser Stress & Slack Responses (Vessel Heave Down).csv', function (error, data){
        
        var stress = [];
        var vesselHeave = [];
        var yieldStrength = [];
        
        data.forEach(function(d){
            
            d.Time = +d.Time;
            d.Stress = +d.Stress;
            d.VesselHeave = +d.VesselHeave;
            d.YieldStrength = +d.YieldStrength;
            
            stress.push({x: d.Time, y: d.Stress});
            vesselHeave.push({x: d.Time, y: d.VesselHeave});
            yieldStrength.push({x: d.Time, y: d.YieldStrength});
            
        });
        
        lineDatas = [
            
            {
                
                key: 'Stress (Elastic)',
                values: stress
                
            },{
                
                key: 'Vessel Heave',
                values: vesselHeave
                
            },{
                
                key: 'Yield Strength (Ksi)',
                values: yieldStrength,
                classed: 'dashed'
                
            }
            
        ];
        
        nv.addGraph(function(){ 
        
            var chart = nv.models.lineWithFocusChart()
                            .useInteractiveGuideline(true)  
                            .showYAxis(true)
                            .showXAxis(true);
            
            chart.height(500);
        
            chart.xAxis
                .axisLabel('Mooring Line Length (m)')
                .tickFormat(d3.format(',.1f'));
        
            chart.forceX([90,200]);
            
            chart.yAxis
                .axisLabel('Effective Tension (mT)')
                .tickFormat(d3.format(',.1f'));
            
            chart.forceY([0, 140]);
        
            d3.select('#chart11 svg') 
                .datum(lineDatas)
                .call(chart);
        
            nv.utils.windowResize(function() { chart.update() }); 
        
            return chart;
        
        });
        
    });
    
}

function riserStressStretchResponses (){
    
    var lineDatas = [];
    
    d3.csv('csv/5.3/Riser Stress & Stretch Response (Vessel Heave Up).csv', function (error, data){
        
        var riserStretch = [];
        var stress = [];
        var yieldStrength = [];
        
        data.forEach(function(d){
            
            d.Time = +d.Time;
            d.RiserStretch = +d.RiserStretch;
            d.Stress = +d.Stress;
            d.YieldStrength = +d.YieldStrength;
            
            riserStretch.push({x: d.Time, y: d.RiserStretch});
            stress.push({x: d.Time, y:d.Stress});
            yieldStrength.push({x:d.Time, y:d.YieldStrength});
            
        });
        
        lineDatas = [
            
            {
                
                key: "Riser Stretch",
                values: riserStretch
                
            }, {
                
                key: "Stress (Elastic)",
                values: stress
                
            }, {
                
                key: "Yield Strength (125 Ksi)",
                values: yieldStrength,
                classed: 'dashed'
                
            }
            
        ];
        
        nv.addGraph(function(){ 
        
            var chart = nv.models.lineWithFocusChart()
                            .useInteractiveGuideline(true)  
                            .showYAxis(true)
                            .showXAxis(true);
            
            chart.height(500);
        
            chart.xAxis
                .axisLabel('Time (s)')
                .tickFormat(d3.format(',.1f'));
        
            chart.forceX([90,200]);
            
            chart.yAxis
                .axisLabel('Stress (Ksi)')
                .tickFormat(d3.format(',.1f'));
            
            chart.forceY([0, 140]);
        
            d3.select('#chart12 svg') 
                .datum(lineDatas)
                .call(chart);
        
            nv.utils.windowResize(function() { chart.update() }); 
        
            return chart;
        
        });
        
    });
    
}

function riserStressResponseRiserSlack() {
    
    var lineDatas = [];
    
    d3.csv('csv/5.3/Stress Response with Riser Slack (Vessel Heave Down).csv', function(error, data){
        
        var stress = [];
        var yieldStrength = [];
        
        data.forEach(function(d){
            
            d.RiserSlack = +d.RiserSlack;
            d.Stress = +d.Stress;
            d.YieldStrength = +d.YieldStrength;
            
            stress.push({x: d.RiserSlack, y: d.Stress});
            yieldStrength.push({x: d.RiserSlack, y: d.YieldStrength});
            
        });
        
        lineDatas = [
            
            {
                
                key: "Stress",
                values: stress
                
            },{
                
                key: "Yield Strength (125 Ksi)",
                values: yieldStrength,
                classed: 'dashed'
                
            }
            
        ];
        
        nv.addGraph(function(){ 
        
            var chart = nv.models.lineWithFocusChart()
                            .useInteractiveGuideline(true)  
                            .showYAxis(true)
                            .showXAxis(true);
            
            chart.height(500);
        
            chart.xAxis
                .axisLabel('Riser Slack (ft)')
                .tickFormat(d3.format(',.1f'));
        
            chart.forceX([0,40]);
            
            chart.yAxis
                .axisLabel('Stress (ksi)')
                .tickFormat(d3.format(',.1f'));
            
            chart.forceY([0, 140]);
        
            d3.select('#chart13 svg') 
                .datum(lineDatas)
                .call(chart);
        
            nv.utils.windowResize(function() { chart.update() }); 
        
            return chart;
        
        });
        
    });
    
}

function stressResponseRiserStretch() {
    
    var lineDatas = [];
    
    d3.csv('csv/5.3/Stress Response with Riser Stretch (Vessel Heave Up).csv', function(error, data){
        
        var stress = [];
        var yieldStrength = [];
        
        data.forEach(function(d){
            
            d.RiserStretch = +d.RiserStretch;
            d.Stress = +d.Stress;
            d.YieldStrength = +d.YieldStrength;
            
            stress.push({x: d.RiserStretch, y: d.Stress});
            yieldStrength.push({x: d.RiserStretch, y: d.YieldStrength});
            
        });
        
        lineDatas = [
            
            {
                
                key: 'Stress (Elastic)',
                values: stress
                
            },{
                
                key: 'Yield Strength (125 ksi)',
                values: yieldStrength,
                classed: 'dashed'
                
            }
            
        ];
        
        nv.addGraph(function(){ 
        
            var chart = nv.models.lineWithFocusChart()
                            .useInteractiveGuideline(true)  
                            .showYAxis(true)
                            .showXAxis(true);
            
            chart.height(500);
        
            chart.xAxis
                .axisLabel('Riser Stretch (ft)')
                .tickFormat(d3.format(',.1f'));
        
            chart.forceX([0,30]);
            
            chart.yAxis
                .axisLabel('Stress (ksi)')
                .tickFormat(d3.format(',.1f'));
            
            chart.forceY([0, 140]);
        
            d3.select('#chart14 svg') 
                .datum(lineDatas)
                .call(chart);
        
            nv.utils.windowResize(function() { chart.update() }); 
        
            return chart;
        
        });
        
    });
    
}
