# WLNG FST Engineering Completion 

<!-- Title Slide -->
## WLNG FST Extreme Weather Analysis

## Inputs and FST

## Vamsee Achanta

<!-- Today's Date -->
<!-- _class: date -->
<script>
  const today = new Date();
  const formattedDate = today.toISOString().split('T')[0];
  document.write(formattedDate);
</script>


---

<!-- Slide for Introduction -->
# Introduction
- FST analysis for WLNG

---
<!-- _class: transition -->

# 

## Design Data

## Analysis Methodology

---

# Design Data - Environment
<div style="display: flex; flex-wrap: wrap; justify-content: space-between;">
  <img src="./plots/metocean/au_input_current.png" alt="Current" style="width: 25%;">
  <img src="./plots/metocean/au_input_wave.png" alt="Wave" style="width: 25%;">
  <img src="./plots/metocean/au_input_wind.png" alt="Wind" style="width: 25%;">
</div>

<div style="text-align: center;">
FST2 &emsp;&emsp;&emsp;&emsp;&emsp; FST1
</div>
<div style="text-align: center;">
  <img src="./plots/fsts.png" alt="Wind" style="width: 35%;">
</div>

```markdown
- Radial plots axis is based on environment direction
```

---
# FSTs Only, General Arrangement

<div style="text-align: center;">
FST2 &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; FST1

![axes](./plots/fsts.png)
</div>

```markdown
- strut, jacket and FST numbering shown
- FST local axes shown
```

---
# Methodology
- TBA

---
# Methodology - Analysis

- TBA

```markdown
- TBA
- TBA
```

---
# Methodology - Result Interpretation

- Timetrace plots are actual values (not statistical)
  - Strut positive tension is tension and negative tension is compression i.e. axes independent values
  - Jacket forces are in global X and Y direction
  - FST forces are in FST local axes
- Radial/rose  plots - ONLY positive values used
  - Objective: 
    - For understanding value change with direction. 
    - The increase/decrease help determine the max force directions.
  - Static values: absolute values
  - Dynamic values: absolute maximum i.e. max (abs(max), abs(min))

```markdown
- Applicable details will be added to each slide
```

---
<!-- _class: transition -->

# 

## 100 year Analysis Results

---
<!-- _class: transition -->

# 

### FST Motion Response

---
# FSTs 95% LNG, 100yr, LWL - FST Surge and Sway

- TBA

<div style="text-align: center;">
FST2 &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; FST1
</div>
<div style="display: flex; justify-content: space-between;">

  <img src="./plots/fsts/au_lwl_100yr_fst2_dof_translation.png" alt="FST2 DOF Translation Plot at 100yr LWL" style="width: 48%;">
  <img src="./plots/fsts/au_lwl_100yr_fst1_dof_translation.png" alt="FST1 DOF Translation Plot at 100yr LWL" style="width: 48%;">
</div>

```markdown
- TBA
```

---
# FSTs 15% LNG, 100yr, HWL - FST Surge and Sway

- TBA

<div style="text-align: center;">
FST2 &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; FST1
</div>
<div style="display: flex; justify-content: space-between;">
    <img src="./plots/fsts/au_hwl_100yr_fst2_dof_translation.png" alt="FST2" style="width: 48%;">
    <img src="./plots/fsts/au_hwl_100yr_fst1_dof_translation.png" alt="FST1" style="width: 48%;">
</div>

```markdown
- TBA
```

---
# FSTs 95% LNG, 100yr, LWL - FST Rotations

- TBA
<div style="text-align: center;">
FST2 &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; FST1
</div>

<div style="display: flex; justify-content: space-between;">
    <img src="./plots/fsts/au_lwl_100yr_fst2_dof_rotation.png" alt="FST1" style="width: 48%;">
    <img src="./plots/fsts/au_lwl_100yr_fst1_dof_rotation.png" alt="FST2" style="width: 48%;">
</div>

```markdown
- TBA
```

---
# FSTs 15% LNG, 100yr, HWL - FST Rotations

- TBA

<div style="text-align: center;">
FST2 &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; FST1
</div>
<div style="display: flex; justify-content: space-between;">
    <img src="./plots/fsts/au_hwl_100yr_fst2_dof_rotation_scale.png" alt="FST1" style="width: 48%;">
    <img src="./plots/fsts/au_hwl_100yr_fst1_dof_rotation_scale.png" alt="FST2" style="width: 48%;">
</div>

```markdown
- TBA
```

---
# FST Rotations, 100 yr, LWL vs. HWL

- TBA

<div style="text-align: center;">
LWL &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; HWL
</div>
<div style="display: flex; justify-content: space-between;">
    <img src="./plots/fsts/au_lwl_100yr_fst2_dof_rotation.png" alt="FST1" style="width: 48%;">
    <img src="./plots/fsts/au_hwl_100yr_fst2_dof_rotation.png" alt="FST2" style="width: 48%;">
</div>

```markdown
- 15% LNG, HWL has low roll rotations compared to 95% LNG, LWL
```

---
<!-- _class: transition -->

# 

### FST Load Response, Static

---
# FSTs 95% LNG, 100yr, HWL, FST Forces, X Direction

- TBA

<div style="text-align: center;">
FST2 &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; FST1
</div>
<div style="display: flex; justify-content: space-between;">
    <img src="./plots/fsts/au_hwl_100yr_fst2_load_Lx_stat.png" alt="FST2" style="width: 48%;">
    <img src="./plots/fsts/au_hwl_100yr_fst1_load_Lx_stat.png" alt="FST1" style="width: 48%;">
</div>

```markdown
- Wind loads dominate the FST forces
```

---
# FSTs 95% LNG, 100yr, HWL, FST Forces, Y Direction

- TBA

<div style="text-align: center;">
FST2 &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; FST1
</div>
<div style="display: flex; justify-content: space-between;">
    <img src="./plots/fsts/au_hwl_100yr_fst2_load_Ly_stat.png" alt="FST1" style="width: 48%;">
    <img src="./plots/fsts/au_hwl_100yr_fst1_load_Ly_stat.png" alt="FST2" style="width: 48%;">
</div>

```markdown
- TBA
```

---
# FSTs 15% LNG, 100yr, LWL, FST Forces, X Direction

- TBA

<div style="text-align: center;">
FST2 &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; FST1
</div>
<div style="display: flex; justify-content: space-between;">
    <img src="./plots/fsts/au_lwl_100yr_fst2_load_Lx_stat.png" alt="FST1" style="width: 48%;">
    <img src="./plots/fsts/au_lwl_100yr_fst1_load_Lx_stat.png" alt="FST2" style="width: 48%;">
</div>

```markdown
- TBA
```

---
# FSTs 15% LNG, 100yr, LWL, FST Forces, Y Direction

- TBA

<div style="text-align: center;">
FST2 &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; FST1
</div>
<div style="display: flex; justify-content: space-between;">
    <img src="./plots/fsts/au_lwl_100yr_fst2_load_Ly_stat.png" alt="FST1" style="width: 48%;">
    <img src="./plots/fsts/au_lwl_100yr_fst1_load_Ly_stat.png" alt="FST2" style="width: 48%;">
</div>

```markdown
- TBA
```

---
<!-- _class: transition -->

# 

### FST Load Response, Dynamic

---
# FSTs 95% LNG, 100yr, HWL, FST Forces, X Direction

- TBA

<div style="text-align: center;">
FST2 &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; FST1
</div>
<div style="display: flex; justify-content: space-between;">
    <img src="./plots/fsts/au_hwl_100yr_fst2_load_Lx.png" alt="FST2" style="width: 48%;">
    <img src="./plots/fsts/au_hwl_100yr_fst1_load_Lx.png" alt="FST1" style="width: 48%;">
</div>

```markdown
- TBA
```

---
# FSTs 95% LNG, 100yr, HWL, FST Forces, Y Direction

- TBA

<div style="text-align: center;">
FST2 &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; FST1
</div>
<div style="display: flex; justify-content: space-between;">
    <img src="./plots/fsts/au_hwl_100yr_fst2_load_Ly.png" alt="FST1" style="width: 48%;">
    <img src="./plots/fsts/au_hwl_100yr_fst1_load_Ly.png" alt="FST2" style="width: 48%;">
</div>

```markdown
- TBA
```

---
# FSTs 15% LNG, 100yr, LWL, FST Forces, X Direction

- TBA

<div style="text-align: center;">
FST2 &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; FST1
</div>
<div style="display: flex; justify-content: space-between;">
    <img src="./plots/fsts/au_lwl_100yr_fst2_load_Lx.png" alt="FST1" style="width: 48%;">
    <img src="./plots/fsts/au_lwl_100yr_fst1_load_Lx.png" alt="FST2" style="width: 48%;">
</div>

```markdown
- TBA
```

---
# FSTs 15% LNG, 100yr, LWL, FST Forces, Y Direction

- TBA

<div style="text-align: center;">
FST2 &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; FST1
</div>
<div style="display: flex; justify-content: space-between;">
    <img src="./plots/fsts/au_lwl_100yr_fst2_load_Ly.png" alt="FST1" style="width: 48%;">
    <img src="./plots/fsts/au_lwl_100yr_fst1_load_Ly.png" alt="FST2" style="width: 48%;">
</div>

```markdown
- TBA
```

