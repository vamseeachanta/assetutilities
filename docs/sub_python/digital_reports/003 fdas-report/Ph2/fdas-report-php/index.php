<?php session_start(); /* Starts the session */

if(!isset($_SESSION['UserData']['Username'])){
	header("location:login.php");
	exit;
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
  <title>Mooring and Riser Analysis Report</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
 
  <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css"/>
  <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>
  <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"></script>
  
  <link href="https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css" rel="stylesheet" integrity="sha384-wvfXpqpZZVQGK6TAh5PVlGOfQNHSoD2xbE+QkPxCAFlNEevoEH3Sl0sibVcOQVnN" crossorigin="anonymous">
  <link rel="stylesheet" href="css/style2.css">
  
   <!-- LINKS TO JS/CSS LIBRARIES -->

        <!-- JS -->
        <script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.0/jquery.min.js"></script>

        <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.2/d3.min.js"></script>
        <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/nvd3/1.8.3/nv.d3.js"></script>

        <script type="text/javascript" src="https://code.jquery.com/ui/1.12.0/jquery-ui.js"></script>
		
		<script src="jquery/jquery.min.js" type="text/javascript"></script>
    <script src="jquery/jquery.printPage.js" type="text/javascript"></script>
	
	<script>  
  $(document).ready(function() {
    $(".btnPrint").printPage();
  });
  </script>
		
		<script>
function openNav() {
    document.getElementById("mySidenav").style.width = "250px";
}

function closeNav() {
    document.getElementById("mySidenav").style.width = "0";
}
</script>
		
	<!-- EXTERNAL FONT(S) -->
        <link href="https://fonts.googleapis.com/css?family=Oswald:300,400|Roboto:300,400" rel="stylesheet">

        <!-- JS EXTERNAL FILES -->
        <script type="text/javascript" src="js/index-charts.js"></script>
		<link href="js/slide.js">
		
		<!-- CSS -->
        <link href="https://cdnjs.cloudflare.com/ajax/libs/nvd3/1.8.3/nv.d3.css" rel="stylesheet"/>

        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/themes/base/jquery-ui.css">
 
  
</head>
<body>

<nav class="navbar navbar-inverse fp">
  <div class="container-fluid">
    <div class="navbar-header">
      <button type="button" class="navbar-toggle" data-toggle="collapse" data-target="#myNavbar">
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>                        
      </button>
      <span class="sn" onclick="openNav()">&#9776; </span>
    </div>
    <div class="collapse navbar-collapse" id="myNavbar">
      <ul class="nav navbar-nav">
        <li class="active"><a href="index.php">Home</a></li>
        
        <li><a href="#">Frontier Deepwater Appraisal Solution Mooring and Riser Analysis Report.</a></li>
      </ul>
      <ul class="nav navbar-nav navbar-right">
		<li>	<a href="#" class="btnPrint"><span class="fa fa-lg fa-print"></span> Print</a></li>
		
        <li><a href="logout.php"><span class="glyphicon glyphicon-log-out"></span> Logout</a></li>
      </ul>
    </div>
  </div>
</nav>

<!--- side bar --->
 <div id="mySidenav" class="sidenav">
  <a href="javascript:void(0)" class="closebtn" onclick="closeNav()">&times;</a>
  
  
   <a href="#introduction">1.Introduction</a>
 
                
                <!-- Summary Navbar -->
               <a href="#summary">2.Summary</a> 
                
                <ul>
              
                 <a href="#2-1-mooring-analysis">2.1 Mooring Analysis</a> 
					<a href="#2-2-riser-analysis">2.2 Riser Analysis</a> 
                    
                
                </ul>
                
                <!-- Design Data Navbar -->
                <a href="#designdata">3.Design Data</a> 
                
                <ul>
						<a href="#3-1-mooring-analysis-data">3.1 Mooring Analysis Data</a>
						<a href="#3-2-riser-data">3.2 Riser Data</a>
                    
						<ul>
							<a href="#3-2-1-internal-fluid">3.2.1 Internal Fluid</a>
							<a href="#3-2-2-stackup">3.2.2 Stack up</a>
						
						</ul>
				
                    
						<a href="#3-3-environmental-data">3.3 Environmental Data</a>
						<a href="#3-4-vessel-data">3.4 Vessel Data</a>
                    
                    <ul>
                        <a href="#3-4-1-Displacement-RAOs">3.4.1 Displacement RAOs</a>
                        <a href="#3-4-2-Load RAOs-Calibrated">3.4.2 Load RAOs Calibrated</a>
                        <a href="#3-4-3-Force-Coefficients">3.4.3 Force Coefficients</a>
						
						
                    
                    </ul>
                    
                </ul>
			
                
                <!-- Analysis Methodology Navbar -->
                <a href="#4-analysis-methodology">4. Analysis Methodology</a>
                
                
                <ul>
					<a href="#4-1-codes-and-standards">4.1 Codes and Standards</a>
                   
					<a href="#4-1-1-Softwares-Used">4.1.1 Softwares Used</a>
                    
					<a href="#4-1-2-Mooring-Analysis">4.1.2 Mooring Analysis</a>
                   
					<a href="#4-1-3-Coupled-Riser-Analysis">4.1.3 Coupled Riser Analysis</a>
					
					<a href="#4-1-4-Riser-Hydrodynamic-Properties">4.1.4 Riser Hydrodynamic Properties</a>
					
					
                
                </ul>
				<a href="#5-results">5.Results</a>
				
				
				<ul>
					<a href="#5-1-mooring-analysis">5.1 Mooring Analysis</a>
					
					<a href="#5-2-rise-stroke">5.2 Riser Stroke with Vessel Offset</a>
					
					<a href="#5-3-riser-response">5.3 Riser Response in 1000 year Hurricane</a>
					
					
				</ul>
				<a href="#6-riser-response-with-vessel">6.Riser Response with Vessel Uniform Heave Speed</a>
				
				<a href="#7-References1">7.References</a>
  
  
  
</div>



<!---side nav ends here---->

<div class="container int" id="#introduction">
  <h2  id="introduction">1. Introduction</h2>
                <p>A semisubmersible drilling vessel is being considered for simultaneous drilling and production activities in deepwater offshore Gulf of Mexico. The frontier deepwater appraisal solution, if feasible will make deepwater drilling of marginal or uncertain fields economical.</p>
		
		<p>To determine the feasiblity of the system, Mooring and Riser Analysis, analysis is conducted as follows:</p>
                   <p> - Determine the mooring configuration to limit the vessel offset to 4% of water depth with all moorings intact </p>
                   <p id="summary"> - Determine the tensioner stroke requirements for 100 year and 1000 year return period hurricane conditions. </p>
                   <p> - Determine the riser response and impact of vessel due to tensioner bottom out (riser  hitting downstop) and riser slack (Riser hitting upstop).</p>
				   
</div>
<!-- SUMMARY SECTION -->
<div class="container" >

	<!-- 2. Summary -->

                    <h2>2. Summary</h2>
                    <p id="2-1-mooring-analysis">Mooring and riser analysis is conducted to determine the feasiblity of the Frontier Deepwater Appraisal solution in approximately 6000 ft water depth fields offshore Gulf of Mexico. The environmental data assumed for the field is representative of Central Gulf of Mexico conditions which are conservative estimates compared to Western Gulf of Mexico. </p>

</div>

<div class="container" id="2-2-riser-analysis">

			<!-- 2.1 Mooring Analysis -->
                
                    <h3>2.1 Mooring Analysis</h3>
                    <p>Mooring analysis is conducted using 8 point and 12 point moorings for 100 year hurricane conditions. The maximum vessel offset with intact mooring conditions is 4.1% of water depth. A 16 point mooring is anticiated to be required to help restrict the vessel offset to 4% offset in 1000 year return period hurricane conditions.
		    </p>

</div>

<div class="container">

			 <!-- 2.2 Riser Analysis -->
                
                    <h3>2.2 Riser Analysis</h3>
                    <p>
		    Coupled riser vessel analysis is conducted to determine the riser response for 1000 year return period hurricane conditions. The key analysis assumptions and results are summarized in this section.</p>
		    
		   <p> The key analysis assumptions for the riser analysis are: </p>
		   <p> - Coupled analysis is conducted using simulated load Response Amplitude Operators (RAOs) so as to take advantage of the decreased vessel motion due to riser stretch forces. Only 2 risers are assumed to be connected to the semi-submersible for 1000 year return period hurricane conditions.</p>
		    <p>- The semi-submersible vessel load RAOs is evaluated as described in Analysis Methodology section.</p>
		    <p>- The tensioner design stroke range is assumed to be 40 ft with 10 ft allocated for upstroke and 30 ft allocated for downstroke. </p>
		    		    
		   <p> The key findings from coupled riser and vessel analysis are summarized below:</p>
		    <p>- The riser tension range in 1000 year hurricane due to riser stretch (vessel heaving up) and riser slack (vessel heaving down) is 1800 kips and 350 kips respectively.</p>
		    <p>- With 2 risers connected, the max stretch stress (at 20 m below tensioner attachment to riser) is 80 ksi while the max slack stress (at bottom) is 60 ksi.</p>
		    <p id="designdata">- When 2 risers are connected to the semi-submersible in 1000 year hurricane conditions, the vessel heave range  decreased by 20% due to the enhanced riser stretch forces </p>
		    <p>- The riser tension and thus the associated stress is expected to marginally decrease further with 4 risers connected. However wave slamming forces on vessel and airgap requirements will need to be understood further.
		    </p>

</div>
 <!-- DESIGN DATA SECTION -->
<div class="container" id="3-1-mooring-analysis-data">
		 <!-- 3.1 Design Data -->
            
                    <h2>3. Design Data</h2>
		
                    <p>The design data used for the mooring and riser analysis is given in the following subsections. </p>

</div>

<div class="container">

	<!-- 3.2 Mooring Analysis Data -->
                
                    <h3>3.1	Mooring Configuration</h3>
			<p>The mooring  configuration used for the mooring analyis is described below:	
                    
                        - The mooring system consists of four groups. <br>
                        - 80 deg, 100 deg, 80 deg, 100 degused between groups to have similar response in both surge and sway directions for 45 deg environmental loading direction.<br>
                        - The mooring system is taut system.<br>
                       <p> - Each mooring line consists of polyester rope with chain at the foundation pile and at the platform (chain-polyester-chain configuration).</p>
                       <p> - 8 and 12 point moorings considered.</p>
			<p>- The mooring properties used for the analysis is given in table below.

			</p>
			

</div>

</br>
</br>
<div class="container">
<div class="col-md-2">
</div>
<div class="col-lg-8">

<div class="table-responsive">

	<table class="table table-striped" border="1">
    <thead>
      <tr>
        <th>Material properties</th>
        <th>Polyester</th>
        <th>Chain</th>
      </tr>
	 
	  
  
    </thead>
    <tbody>
      <tr>
        <td>Geometry (Outer diameter)</td>
        <td>0.305</td>
        <td>0.254</td>
		
      </tr>
      <tr>
        <td>Size of Material</td>
        <td>14</td>
        <td>10</td>
		
      </tr>
      <tr>
        <td>Mass per unit Length(te/m)</td>
        <td>0.101</td>
        <td>1.284</td>
		        
      </tr>
	  <tr>

                            <td>Axial Stiffnes(kN)</td>
                            <td>1.4E5</td>
                            <td>5.50E+06</td>

                        </tr>

                        <tr>

                            <td>Construction type, Link type</td>
                            <td>Polyester (8- strand Multiplait)</td>
                            <td>Stud less</td>

                        </tr>

                        <tr>

                            <td>Data (Rope, chain, Nominal diameter) (m)</td>
                            <td>0.355</td>
                            <td>0.457</td>

                        </tr>

                        <tr>

                            <td>Min. Breaking load (Te)</td>
                            <td>2190</td>
                            <td>2134</td>

                        </tr>
	  
	  
    </tbody>
  </table>
	
<p class="img_arial" id="3-2-riser-data"><i>Table 1 - Properties of Mooring Lines</i></p>
</div>
</div>
</div>

</br>
</br>

<div class="container" id="3-2-1-internal-fluid">

<!-- 3.2 Riser Data -->
                
                    <h3>3.2 Riser Data</h3>
			<p id="3-2-2-stackup"> The data used for riser analysis is given in this section. The riser Stack-up drawing and data are also given in section.  <br>
			</p>

</div>

<div class="container">

			<!-- 3.3.1 Internal Fluid -->
                        
                        <h3>3.2.1 Internal Fluid</h3>
                    
                        <p>The internal fluid is assumed to be seawater and the density is assumed to be 8.55 ppg (1025 kg/m^3).</p>

</div>

<div class="container">

		<h3>3.2.2 Stack up</h3>

<p> The Riser Stack Up used for analysis is shown in Figure below and properties are summarized in Table below. </p> 

</div>
<br>
<br>
<br>

<div class="container">
<div class="col-md-4">
</div>
<div class="col-lg-4">

<img src="pictures/StackUp.png" class="img-responsive" alt="Figure - Riser Stack up.">
<p class="img_arial"><i>Figure - Riser Stack up</i></p>

</div>
</div>

<br>
<br>

<div class="container">
<div class="col-md-4">
</div>
<div class="col-md-4">

<img src="pictures/StackUp Table.png" class="img-responsive" alt="Table - Riser Stack up">
<p class="img_arial" id="3-3-environmental-data"><i>Table 2 - Riser Stack up</i></p>

</div>
</div>

</br>
</br>
</br>
</br>
</br>
</br>

<div class="container">

		<h3>3.3 Environmental Data</h3>
			<p style="font-family:arial"> The 100 year and 1000 year hurricane and the associated current speed are given in this section. The high tide  and low tide and associated storm surge are also given in this section. </p>
			</div>
	

</br>
</br>

<div class="container">
<div class="col-md-2">
</div>
<div class="col-lg-8">

<div class="table-responsive">

	<table class="table table-striped" border="1">
    <thead>
      <tr>
        <th rowspan="2">Descrpition</th>
        <th rowspan="2">Units</th>
        <th colspan="2">100 year Hurricane</th>
		<th colspan="2">1000 year Hurricane</th>
      </tr>
	 
	  <tr>
	
    <th scope="col">Central GoM</th>
    <th scope="col">Western GoM</th>
    <th scope="col">Central GoM</th>
	<th scope="col">Western GoM</th>
  </tr>
  
    </thead>
    <tbody>
      <tr>
                        <td>Significant wave height, Hs</td>                              
						<td>m</td>
                        <td>15.8</td>
                        <td>14</td>
                        <td>19.8</td>
                        <td>17</td>
						</tr>
						
						
                        <tr>

                            <td>Maximum Wave Height, Hmax</td>
                            <td>m</td>
                            <td>27.9</td>
                            <td>24.7</td>
                            <td>34.9</td>
                            <td>30.9</td>

                        </tr>

                        <tr>
                            

                            <td>Maximum Crest Elevation</td>
                            <td>m</td>
                            <td>18.1</td>
                            <td>15.9</td>
                            <td>22.5</td>
                            <td>19.8</td>

                        </tr>

                        <tr>

                            <td>Peak Spectral Period, TP</td>
                            <td>s</td>
                            <td>15.4</td>
                            <td>15.2</td>
                            <td>17.2</td>
                            <td>17</td>

                        </tr>

                        <tr>

                            <td>Associated Maximum period, Tmax</td>
                            <td>s</td>
                            <td>13.9</td>
                            <td>13.7</td>
                            <td>15.5</td>
                            <td>15.3</td>

                        </tr>
    </tbody>
  </table>
	<p class="img_arial"><i>Table 3 - Hurricane Data</i></p>

</div>
</div>	
</div>                   


</br>
</br>

<div class="container">
<div class="col-md-2">
</div>
<div class="col-lg-8">
<div class="table-responsive">

	<table class="table table-striped" border="1">
    <thead>
      <tr>
        <th rowspan="3">Water Depth (m)</th>
        <th colspan="2">Current Associated with 100 year Hurricane</th>
        <th colspan="2">Current Associated with 1000 year Hurricane</th>
		
      </tr>
	 <tr>
			
					
		<th colspan="2">Current Speed(m/s)</th>
		<th colspan="2"></th>
		</tr>
	 
	  <tr>
	<th scope="col">Central GoM</th>
		<th scope="col">Western GoM</th>
    <th scope="col">Central GoM</th>
    <th scope="col">Western GoM</th>
    
  </tr>
  
    </thead>
    <tbody>
      <tr>   
                            
                            <td>0.0</td>
                            <td>2.4</td>
                            <td>2</td>
                            <td>3</td>
                            <td>2.6</td>
                            
				        </tr>
                
						<tr> 
                            
                            <td>100.0</td>
                            <td>2.4</td>
                            <td>2</td>
                            <td>3</td>
                            <td>2.6</td>
                            
                        </tr>
                    
						<tr>   
                            
                            <td>914.4</td>
                            <td>1.8</td>
                            <td>1.5</td>
                            <td>2.25</td>
                            <td>2</td>
                            
                        </tr>
						 
                
                        <tr>   
                            
                            <td>1728.8</td>
                            <td>0.3</td>
                            <td>0.3</td>
                            <td>0.3</td>
                            <td>0.3</td>
                            
                        </tr>
						 
                        <tr>  
                            
                            <td>1828.8</td>
                            <td>0</td>
                            <td>0</td>
                            <td>0</td>
                            <td>0</td>
                            
                        </tr>
    </tbody>
  </table>
	<p class="img_arial"><i>Table 4 - Currents Associated with Extreme Hurricanes in GoM, API RP 2MET</i></p>

</div>
</div>
</div>


</br>
</br>	  
	  
<div class="container">
<div class="col-md-2">
</div>
<div class="col-lg-8">
<div class="table-responsive">

	<table class="table table-striped" border="1">
    <thead>
      <tr>
        <th>High Tide (m)</th>
        <th >Low Tide (m)</th>
        <th >Storm Surge (m)</th>
		
      </tr>
	  </thead>
    <tbody>
	<tr>
							<td >0.5</td>
							<td >0.5</td>
							<td >0.9</td>
					
	</tr>
	</tbody>
  </table>
  <p class="img_arial" id="3-4-vessel-data"><i>Table 5 - Tide and Storm Surge in 1000 yr Storm Conditions</i></p>
  </div>
</div>
</div>


</br>
</br>

<div class="container">

		<h3 id="3-4-1-Displacement-RAOs">3.4	Vessel Data</h3>
		<p style="font-family:arial"> The vessel data used for analysis is given in this section. </p>

</div>

<div class="container">

	<h3>3.4.1 Displacement RAOs</h3>
	<p style="font-family:arial"> The displacement RAO data used for analysis is given in this section. The analysis conducted is conducted for 45 deg wave heading and the associated RAO is shown below. </p>

</div>

<div class="container">
<div class="col-md-2">
</div>
<div class="col-md-6">

<img src="pictures/Disp. RAO.png" class="img-responsive"  alt="Figure - Riser Stack up.">
<p id="3-4-2-Load RAOs-Calibrated"></p>
<br>

<p class="img_arial" ><i>Figure 2 - Vessel RAOs for 45 deg Wave Heading</i></p>


</div>
</div>

<div class="container">

		<h3>3.4.2 Load RAOs Calibrated</h3>
		<p style="font-family:arial">The load RAOs are calibrated and matched with the heave of the vessel in displacement Raos for 1000 yr hurricane wave conditions (height and period) without any risers connected. The key data assumptions are:
						<br>
						The key data assumed for this calibration are: <br>
						- 43000 mT of Semi mass<br>
						- Associated added mass and damping<br>
						<p id="3-4-3-Force-Coefficients">- Approximate peak heave load RAO obtained from calibration is 22.4 kips/ft</p>
						<p >- Regular wave analysis to simulate 1000 yr hurricane. Both max wave height seed and nominal seed simulated.
						</p>

</div>

<div class="container">

	<h3>3.4.3 Force Coefficients </h3>

                        <p style="font-family:arial">The wind and current force coefficients used for the analysis are shown below</p>

</div>

<div class="container">

		<div class="col-md-2">
</div>
<div class="col-md-6">

<img src="pictures/Current 20m draft Force Coefficient.png" class="img-responsive" alt="Figure - Riser Stack up.">
<p class="img_arial"><i>Figure 1-Current 20m draft Force Coefficient</i></p>

</div>

</div>

<div class="container">

		<div class="col-md-2">
</div>
<div class="col-md-6">

<img src="pictures/Current 20m draft Moment Coefficient.png" class="img-responsive" alt="Figure - Riser Stack up.">
<p class="img_arial"><i>Figure 2-Current 20m draft Moment Coefficient</i></p>

</div>

</div>

<div class="container">

		<div class="col-md-2">
</div>
<div class="col-md-6">

<img src="pictures/Wind 20m draft Force Coefficient.png" class="img-responsive" alt="Figure - Riser Stack up.">
<p class="img_arial"><i>Figure 3-Wind 20m draft Force Coefficient</i></p>

</div>

</div>

<div class="container">

		<div class="col-md-2">
</div>
<div class="col-md-6">

<img src="pictures/Wind 20m draft Moment Coefficient.png" class="img-responsive" alt="Figure - Riser Stack up.">

<p id="4-analysis-methodology"></p>
<br>
<p class="img_arial" ><i>Figure 4-Wind 20m draft Moment Coefficient</i></p>

</div>

</div>

<div class="container">

		<h2>4. Analysis Methodology</h2>
		 <p style="font-family:arial" id="4-1-codes-and-standards"> The analysis methodology used for the mooring and riser analysis is given in this section.</p>
</div>
<br>
<div class="container">
		<h3>4.1	Codes and Standards </h3>
		<p style="font-family:arial" id="4-1-1-Softwares-Used">The codes and standards proposed for the analysis are given in Reference section. The calculations to be performed in later stages of the project will be performed utilzing these codes and standards.</p>
</div>

<div class="container">

		<h3 id="4-1-2-Mooring-Analysis">4.1.1	Softwares Used </h3>
	
	   <p style="font-family:arial" >3D finite element analysis software, OrcaFlex is utilized for analysis.</p>

</div>

<div class="container">
		
		<h3>4.1.2	Modelling </h3>
		
		<p style="font-family:arial" id="4-1-3-Coupled-Riser-Analysis"> The mooring and Riser FEA model is simulated with appropriate structural properties mooring model with appropriate line properties along the length. 
		</p>
		
</div>
<br>

<div class="container">
		
		<h3>4.1.3	Coupled Riser Analysis</h3>
		<p style="font-family:arial">
		
		Coupled riser analysis is conducted by utilizing the following: <br>
		<p >- Load RAOs to simulate wave forces on the vessel.</p>
		<p>- Tensioner stiffness curve for both upstroke and downstroke to simulate riser stretch and slack as shown below.</p>
		
</div>

<div class="container">
			
			<div class="col-md-2">
</div>
<div class="col-md-6">

<img src="pictures/tensioner.jpg" class="img-responsive" alt="Figure - Riser Stack up.">
<p class="img_arial" ><i>Figure 1 - Tensioner Force vs Displacement Curve</i></p>

</div>
			
</div>
<p id="4-1-4-Riser-Hydrodynamic-Properties"></p>
<br>
<br>
<div class="container" >
		
		<h3>4.1.4 Riser Hydrodynamic Properties</h3>
					
					<p style="font-family:arial">The riser hydrodynamic properties used for analysis are: <br>
				- A constant normal drag coefficient of 1.2 is used for the analysis. <br>
				- An axial drag coefficient of 0.1 is used for 1000 year hurricane dynamic analysis. <br>
				- An axial drag coefficient of 0.5 is used for uniform vessel heave analysis. <br>
				- The normal and axial drag coefficient directions of the pipe are shown below.</p>
		
</div>

<div class="container">
		
		<div class="col-md-2">
</div>
<div class="col-md-6">

<img src="pictures/fig-36.png" class="img-responsive" alt="Figure - Riser Stack up.">
<p class="img_arial"><i>Figure 4 -Normal and Axial Drag With Respect Pipe Motion Direction </i></p>

</div>
		
</div>
<p id="5-results"></p>
<br>
<br>
<p id="5-1-mooring-analysis"></p>
<br>
 <!-- ANALYSIS METHODOLOGY -->
<div class="container">
		
		 <h2>5. Results</h2>
		 <h3>5.1	Mooring Analysis</h3>

                        <p style="font-family:arial">The mooring analysis is conducted on vessel with 8 and 12 point mooring configurations. The configurations are sets in such a way to obtain a lateral offset of 4% during the 100 years hurricane conditions. The nominal tension is also adjusted in the configurations such that it is 1/3 of the total minimum breaking load (MBL).</p> 

                        <p style="font-family:arial">The configurations for 8 point and 12 point mooring are shown in Table 6 and Table 7 with the illustrations in Figure 3 and Figure 4 respectively.</p>
</div>


</br>
</br>

<div class="container">
<div class="col-md-2">
</div>
<div class="col-lg-8">
<div class="table-responsive">

	<table class="table table-striped" border="1">
    <thead>
      <tr>
        <th>Configuration</th>
        <th>Horizontal Distance to Anchor</th>
         <th>Polyester Rope Length</th>
          <th>Polyester rope length</th>
          <th>Top Chain Length</th>
            <th>chain</th>
          <th>Bottom Chain Length</th>
          <th>Max. Offset</th>
          <th>Nominal Eff. Tension</th>
      </tr>
	  </thead>
    <tbody>
			
			<tr>

                                <td>Units</td>
                                <td>m</td>
                                <td>m</td>
                                <td>Inches</td>
                                <td>m</td>
                                <td>Inches</td>
                                <td>m</td>
                                <td>%</td>
                                <td>mT</td>

                            </tr>

                            <tr>

                                <td>1</td>
                                <td>2421</td>
                                <td>2600</td>
                                <td>14</td>
                                <td>100</td>
                                <td>10</td>
                                <td>250</td>
                                <td>6.1</td>
                                <td>450</td>

                            </tr>

                            <tr>

                                <td>2</td>
                                <td>2421</td>
                                <td>2621</td>
                                <td>14</td>
                                <td>100</td>
                                <td>10</td>
                                <td>250</td>
                                <td>6.6</td>
                                <td>570</td>

                            </tr>

                            <tr>

                                <td>3</td>
                                <td>2421</td>
                                <td>2560</td>
                                <td>14</td>
                                <td>100</td>
                                <td>10</td>
                                <td>250</td>
                                <td>5.3</td>
                                <td>830</td>

                            </tr>

                            <tr>

                                <td>4</td>
                                <td>2421</td>
                                <td>2580</td>
                                <td>14</td>
                                <td>100</td>
                                <td>10</td>
                                <td>250</td>
                                <td>5.6</td>
                                <td>737</td>

                            </tr>
			
	</tbody>
  </table>
  <p class="img_arial"><i>Table 7 - Configuration vs Results for 8 point Mooring Lines</i></p>
  </div>
</div>
</div>


</br>
</br>

<div class="container">
<div class="col-md-2">
</div>
<div class="col-lg-8">
<div class="table-responsive">

	<table class="table table-striped" border="1">
    <thead>
      <tr>
        <th>Configuration</th>
        <th>Horizontal Distance to Anchor</th>
         <th>Polyester Rope Length</th>
          <th>Polyester rope length</th>
          <th>Top Chain Length</th>
            <th>chain</th>
          <th>Bottom Chain Length</th>
          <th>Max. Offset</th>
          <th>Nominal Eff. Tension</th>
      </tr>
	  </thead>
    <tbody>
			
			<tr>

                                <td>Units</td>
                                <td>m</td>
                                <td>m</td>
                                <td>Inches</td>
                                <td>m</td>
                                <td>Inches</td>
                                <td>m</td>
                                <td>%</td>
                                <td>mT</td>

                            </tr>

                            <tr>

                                <td>1</td>
                                <td>2421</td>
                                <td>2600</td>
                                <td>14</td>
                                <td>100</td>
                                <td>10</td>
                                <td>250</td>
                                <td>4.4</td>
                                <td>450</td>

                            </tr>

                            <tr>

                                <td>2</td>
                                <td>2421</td>
                                <td>2621</td>
                                <td>14</td>
                                <td>100</td>
                                <td>10</td>
                                <td>250</td>
                                <td>4.8</td>
                                <td>570</td>

                            </tr>

                            <tr>

                                <td>3</td>
                                <td>2421</td>
                                <td>2560</td>
                                <td>14</td>
                                <td>100</td>
                                <td>10</td>
                                <td>250</td>
                                <td>3.8</td>
                                <td>830</td>

                            </tr>

                            <tr>

                                <td>4</td>
                                <td>2421</td>
                                <td>2580</td>
                                <td>14</td>
                                <td>100</td>
                                <td>10</td>
                                <td>250</td>
                                <td>4.1</td>
                                <td>737</td>

                            </tr>
			
	</tbody>
  </table>
 <p class="img_arial"><i>Table 8 - Configuration vs Results for 12 point Mooring Lines</i></p>
  </div>
</div>
</div>


</br>
</br>

<div class="container">
	
	 <p style="font-family:arial">The wave, wind and currents are applied in 45 deg direction to the vessel. <br> - The offset positions of the vessel with the 8 point mooring and 12 point mooring are shown in the Figure 4 and Figure 5 respectively. <br> 
- With the 12 point mooring the vessel is at offset of 4.1% of the water depth. <br> 
- The effective tension of 8 point mooring for mooring lines 1 and 6 are shown in Figure 6 and Figure 7. <br>
- The effective tension of 12 point mooring lines 1 and 8 are shown in Figure 8 and Figure 9.
			
			</p>

                        <p style="font-family:arial">The 12 point mooring is considered for the evaluation of the detailed riser response analysis</p>		
	
</div>

<div class="container">
		
		<div class="col-md-2">
</div>
<div class="col-md-6">

<img src="pictures/8P.png" class="img-responsive" alt="Figure - Riser Stack up.">
<p class="img_arial"><i>Figure 5 - Mooring Configuration for 8 Point Moorings</i></p>

</div>
		
</div>

<div class="container">
		
		 <div class="chart-container ch" id="chart8">

                                          <svg></svg>

                            </div>
							

							<p class="img_arial"><i>Chart 1 - Vessel Position for 8 Point Mooring</i></p>

</div>

<div class="container">
		
		<div class="col-md-2">
</div>
<div class="col-md-6">

<img src="pictures/12P.png" class="img-responsive" alt="Figure - Riser Stack up.">
<p class="img_arial"><i>Figure 6 - Mooring Configuration for 12 Point Moorings</i></p>

</div>
		
</div>

<div class="container">
                            <div class="chart-container ch" id="chart9">

                                
                                <svg></svg>

                            </div>
							<p class="img_arial"><i>Chart 2 - Vessel Position for 12 Point Mooring</i></p>

</div>

<div class="container">
	<div class="chart-container ch" id="chart1">

                                  <svg></svg>
									<p class="img_arial"><i>Chart 3 - Effective Tension Along Lowest Tension Mooring (Line1) for 8 point Mooring</i></p>
                            </div>
</div>							

<div class="container">

		<div class="chart-container ch" id="chart2">

                               
                                <svg></svg>

                            </div>
							<p class="img_arial"><i>Chart 4 - Effective Tension Along Highest Tension Mooring (Line6) for 8 point Mooring </i></p>

</div>

<div class="container">

			<div class="chart-container ch" id="chart3">

                                
                                <svg></svg>

                            </div>
							<p class="img_arial"><i>Chart 5 - Effective Tension Along Lowest Tension Mooring (Line1) for 12 point Mooring</i></p>

</div>

<div class="container">

			<div class="chart-container ch" id="chart4">

                               
                                <svg></svg>

                            </div>
							<p class="img_arial" id="5-2-rise-stroke"><i>Chart 6 - Effective Tension ALong Highest Tension Mooring (Line8) for 12 point Mooring</i></p>

</div>
<br>
<div class="container">

			<h3>5.2 Riser Stroke with Vessel Offset </h3>
<p> The riser stroke with vessel offset is given below.</p>
			<div class="chart-container ch" id="chart7">

                        
                        <svg></svg>

                    </div>
					<p class="img_arial"><i>Chart 7 - Stroke (ft) vs. Offset</i></p>
                
                </div>
						
					</div>	

</div>
<p id="5-3-riser-response"></p>
<br>
<br>
<div class="container">

	<h3>5.3 Riser Response in 1000 year Hurricane </h3>
                        
                        <p style="font-family:arial">Riser analysis is conducted for 1000 year return period hurricane conditions with the following simplified assumptions: </p>
                        
<p>- No buoyancy is considered at top of region. </p>
<p>- The riser is modeled as a single Casing pipe. </p>
<p>- Tension factor of 1.4 with top tension of approximately 800 kips. </p>
<p>- Tide and storm surge are assumed for the stroke analysis. </p>
<p>- Riser stroke due to pressure and thermal expansion is not considered as riser is assumed to be not producing. </p>

<p>Riser analysis for 1000 year hurricane conditions and the results are summarized below: </p>
<p>- The riser stretch and slack relative to upstop and downstops are show below. The various stroke contributions are also shown. </p>
<p>- The effective tension, lateral displacment and stress response along the length of the riser is shown below.</p>



</div>

<div class="container">

	<div class="col-md-2">
</div>
<div class="col-md-6">

<img src="pictures/RISER STROKE AND VESSEL POSITION 1000yr Hurricane.png" class="img-responsive" >
<p class="img_arial"><i>Figure 7 - Riser Stroke and Vessel Position in 1000yr Hurricane</i></p>

</div>

</div>

<div class="container">

	<div class="col-md-2">
</div>
<div class="col-md-6">

<img src="pictures/Effective Tension Along the Riser length(Top 100ft).png" class="img-responsive fh" >
<p class="img_arial"><i>Figure 12 - Effective Tension Along the Riser length(Top 100ft)</i></p>

</div>

</div>

<div class="container">

	<div class="col-md-2">
</div>
<div class="col-md-6">

<img src="pictures/Effective Tension Along the Riser length 11.png" class="img-responsive fh" >
<p class="img_arial"><i>Figure 13 - Effective Tension Along the Riser length</i></p>

</div>

</div>

<div class="container">

	<div class="col-md-2">
</div>
<div class="col-md-6">

<img src="pictures/Lateral Displacement Along the Length of  Riser during Stretch.png" class="img-responsive fh" >
<p class="img_arial"><i>Figure 14 - Lateral Displacement Along the Length of  Riser during Stretch</i></p>

</div>

</div>

<div class="container">

	<div class="col-md-2">
</div>
<div class="col-lg-4">

<img src="pictures/Stress (ksi) along the Length of the Riser during Strech(Top 100ft).png" class="img-responsive fh" >
<p class="img_arial"><i>Figure 15 - Stress (ksi) along the Length of the Riser during Strech(Top 100ft)</i></p>

</div>

</div>

<div class="container">

	<div class="col-md-2">
</div>
<div class="col-md-6">

<img src="pictures/Stress (ksi) along the Length of the Riser during Strech.png" class="img-responsive fh" >
<p class="img_arial" id="6-riser-response-with-vessel"><i>Figure 16 - Stress (ksi) along the Length of the Riser during Strech</i></p>

</div>

</div>
<br>
<div class="container">

	<h2>6. Riser Response with Vessel Uniform Heave Speed </h2>
<p style="font-family:arial"> Riser response analysis is conducted using vessel uniform heave speed up or down. The riser stretch and slack responses are assessed and the results are given in this section.</p>
<p>- The riser stress response and riser stretch during vessel heaving up is shown below. </p>
<p>- The riser stress response and riser slack during vessel heaving down is shown below. </p>
<p>- The animation of the riser response with vessel heaving down is also shown.</p>

</p>

</div>

<div class="container">

	<div class="col-md-2">
</div>
<div class="col-md-6">

<img src="pictures/Riser Stress & Stretch Response (Vessel Heave Up).png" class="img-responsive" >
<p class="img_arial"><i>Figure 11 - Riser Stress & Stretch Response (Vessel Heave Up)</i></p>

</div>

</div>

<div class="container">

	<div class="col-md-2">
</div>
<div class="col-md-6">

<img src="pictures/Stress Response with Riser Stretch (Vessel Heave Up).png" class="img-responsive">
<p class="img_arial"><i>Figure 9 - Stress Response with Riser Stretch (Vessel Heave Up)</i></p>

</div>

</div>

<div class="container">

	<div class="col-md-2">
</div>
<div class="col-md-6">

<img src="pictures/Riser Stress & Slack Responses (Vessel Heave Down).png" class="img-responsive">
<p class="img_arial"><i>Figure 10 - Riser Stress & Slack Responses (Vessel Heave Down)</i></p>

</div>

</div>

<div class="container">

	<div class="col-md-2">
</div>
<div class="col-md-6">

<img src="pictures/Stress Response with Riser Slack (Vessel Heave Down).png" class="img-responsive" >
<p class="img_arial"><i>Figure 8 - Stress Response with Riser Slack (Vessel Heave Down)</i></p>

</div>

</div>



<div class="container">
	<div class="col-md-2">
	</div>
	<div class="col-md-4">
	<video controls> 
  
  
   <source src="video/ro_slack.mp4" type="video/mp4"> 
   
</video>
</div>
</div>
 


<div class="container">

		<h2 id="7-References1">7.References </h2>
<p style="font-family:arial"> [1] API, " Design and Analysis of Stationkeeping Systems for Floating Structures ", API RP 2SK, 2005</p>
<p style="font-family:arial"> [2] API, "Synthetic Fiber Ropes for Mooring", API RP 2SM 1st Ed & Addendum (2001 & 2007)</p>
<p style="font-family:arial"> [3] API, "Derivation of Metocean Design and Operating Conditions", API-RP-2MET, November 2014.</p>
<p style="font-family:arial"> API RP-2RD</p>

</div>



</body>
</html>