$(document).ready(function() {
    
    //Sidenav JScript
    
    $(document).scroll(function(){
         
        var offsetPixel = 23;
         
        if($(window).scrollTop() > offsetPixel) {
             
            $('#sidebar').css('position', 'fixed');
            $('#sidebar').css('top', 0);
            $('#sidebar').css('width', '20%');
             
        } else { 
             
            $('#sidebar').css('position', 'static');
            $('#sidebar').css('top', 0);
            $('#sidebar').css('width', '100%');
             
        }
    });    
    
    //Calling the graphs
    
    linechart1();
    linechart2();
    linechart3();
    linechart4();
    linechart5();
    linechart6();
    linechart7();
    
    scatterChart();
    scatterChart2();
    
    
    
});
    
//Sidebar links JScript

function scrollToDiv(div) {
    
    $('html, body').animate({
		scrollTop: $(div).offset().top
	},1000);
    
    }

function linechart1() {
    
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
        
            var chart = nv.models.lineChart()
                            .useInteractiveGuideline(true) //Self explanatory 
                            .showYAxis(true)
                            .showXAxis(true);
            
            chart.height(500); //Height of the graph in px
        
            chart.xAxis
                .axisLabel('Mooring Line Length (m)'); // Labelling the x axis
        
            chart.forceX([0,3250]); //This forces the graph to have a minimum point of 0 and a maximum point of 3250
            
            chart.yAxis
                .axisLabel('Effective Tension (mT)');
            
            chart.forceY([0,100,200,300,400,500,600,700,800]);
        
            d3.select('#chart1 svg') //This is where the graph will be placed
                .datum(lineData) //Passing in the graph data
                .call(chart); //calling the chart
        
            nv.utils.windowResize(function() { chart.update() }); //This reformats the graph after the user window has been resized
        
            return chart; //This basically calls the chart into the website
        
        });
        
    });
    
}

function linechart2() {
    
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
        
            var chart = nv.models.lineChart()
                            .useInteractiveGuideline(true)  
                            .showYAxis(true)
                            .showXAxis(true);
            
            chart.height(500);
        
            chart.xAxis
                .axisLabel('Mooring Line Length (m)');
        
            chart.forceX([0,3250]);
            
            chart.yAxis
                .axisLabel('Effective Tension (mT)');
            
            chart.forceY([0, 1200]);
        
            d3.select('#chart2 svg') 
                .datum(lineData)
                .call(chart);
        
            nv.utils.windowResize(function() { chart.update() }); 
        
            return chart;
        
        });
        
    });    
    
}

function linechart3() {
    
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
        
            var chart = nv.models.lineChart()
                            .useInteractiveGuideline(true)  
                            .showYAxis(true)
                            .showXAxis(true);
            
            chart.height(500);
        
            chart.xAxis
                .axisLabel('Mooring Line Length (m)');
        
            chart.forceX([0,3250]);
            
            chart.yAxis
                .axisLabel('Effective Tension (mT)');
            
            chart.forceY([0, 800]);
        
            d3.select('#chart3 svg') 
                .datum(lineData)
                .call(chart);
        
            nv.utils.windowResize(function() { chart.update() }); 
        
            return chart;
        
        });
        
    });
    
}

function linechart4() {
    
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
        
            var chart = nv.models.lineChart()
                            .useInteractiveGuideline(true)  
                            .showYAxis(true)
                            .showXAxis(true);
            
            chart.height(500);
        
            chart.xAxis
                .axisLabel('Mooring Line Length (m)');
        
            chart.forceX([0,3250]);
            
            chart.yAxis
                .axisLabel('Effective Tension (mT)');
            
            chart.forceY([0, 1200]);
        
            d3.select('#chart4 svg') 
                .datum(lineData)
                .call(chart);
        
            nv.utils.windowResize(function() { chart.update() }); 
        
            return chart;
        
        });
        
    });
    
}

function linechart5() {
    
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
        
            var chart = nv.models.lineChart()
                            .useInteractiveGuideline(true)  
                            .showYAxis(true)
                            .showXAxis(true);
            
            chart.height(500);
        
            chart.xAxis
                .axisLabel('Distance (m)');
        
            chart.forceX([100,200]);
            
            chart.yAxis
                .axisLabel('Time (s)');
            
            chart.forceY([-10, 70]);
        
            d3.select('#chart5 svg') 
                .datum(lineData)
                .call(chart);
        
            nv.utils.windowResize(function() { chart.update() }); 
        
            return chart;
        
        });
        
    });
    
}

function linechart6() {
    
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
        
            var chart = nv.models.lineChart()
                            .useInteractiveGuideline(true)  
                            .showYAxis(true)
                            .showXAxis(true);
            
            chart.height(500);
        
            chart.xAxis
                .axisLabel('Time (s)');
        
            chart.forceX([100,200]);
            
            chart.yAxis
                .axisLabel('Distance (m)');
            
            chart.forceY([-80, 20]);
        
            d3.select('#chart6 svg') 
                .datum(lineData)
                .call(chart);
        
            nv.utils.windowResize(function() { chart.update() }); 
        
            return chart;
        
        });
        
    });
    
}

function linechart7() {
    
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
        
            var chart = nv.models.lineChart()
                            .useInteractiveGuideline(true)  
                            .showYAxis(true)
                            .showXAxis(true);
            
            chart.height(500);
        
            chart.xAxis
                .axisLabel('Offset (%)');
        
            chart.forceX([-2,10]);
            
            chart.yAxis
                .axisLabel('Stroke (ft)');
            
            chart.forceY([-22, 0]);
        
            d3.select('#chart7 svg') 
                .datum(lineData)
                .call(chart);
        
            nv.utils.windowResize(function() { chart.update() }); 
        
            return chart;
        
        });
        
    });
    
}

function scatterChart() {
    
    var scatterData = [];
    
    d3.csv('csv/VesselPosition_8Point.csv', function(error, data) {
        
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
                .axisLabel('Surge (m)');
            
            chart.forceX([-10,100]);
            
            chart.yAxis
                .axisLabel('Sway (m)');
            
            chart.forceY([-10, 100]);
            
            d3.select('#chart8 svg') 
                .datum(scatterData)
                .call(chart);
        
            nv.utils.windowResize(function() { chart.update() }); 
        
            return chart;
            
        });
        
    });
    
}

function scatterChart2() {
    
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
                .axisLabel('Surge (m)');
            
            chart.forceX([-10,60]);
            
            chart.yAxis
                .axisLabel('Sway (m)');
            
            chart.forceY([-10, 60]);
            
            d3.select('#chart9 svg') 
                .datum(scatterData)
                .call(chart);
        
            nv.utils.windowResize(function() { chart.update() }); 
        
            return chart;
            
        });
        
    });
    
}