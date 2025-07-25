# release-MC_25km_jra_ryf

## Model Configuration Overview

ACCESS-OM3 is a coupled ocean-sea ice model using MOM6 (ocean) and CICE (sea-ice). The 25km global configuration uses a tripolar grid to avoid a singularity at the North Pole. The domain is zonally periodic ([`REENTRANT_X = True`](https://github.com/ACCESS-NRI/access-om3-configs/blob/408715d5f0a53b105de1ec33cf5676c5d5211ee1/docs/MOM_parameter_doc.all#L192)) and open at the north via a tripolar fold ([`TRIPOLAR_N = True`](https://github.com/ACCESS-NRI/access-om3-configs/blob/408715d5f0a53b105de1ec33cf5676c5d5211ee1/docs/MOM_parameter_doc.all#L196)) while closed in the south ([`REENTRANT_Y = False`](https://github.com/ACCESS-NRI/access-om3-configs/blob/408715d5f0a53b105de1ec33cf5676c5d5211ee1/docs/MOM_parameter_doc.all#L194)). The horizontal grid has [`1440x1142`](https://github.com/ACCESS-NRI/access-om3-configs/blob/408715d5f0a53b105de1ec33cf5676c5d5211ee1/docs/MOM_parameter_doc.all#L199-L202) tracer points. Vertically, the ocean is discretised into 75 layers ([`NK=75`](https://github.com/ACCESS-NRI/access-om3-configs/blob/408715d5f0a53b105de1ec33cf5676c5d5211ee1/docs/MOM_parameter_doc.all#L331)) using a [`zstar` coordinate](https://github.com/ACCESS-NRI/access-om3-configs/blob/408715d5f0a53b105de1ec33cf5676c5d5211ee1/docs/MOM_parameter_doc.all#L455), with partial cells to represent bottom topography. This matches the resolution of prior models (eg ACCESS-OM2-025 and GFDL OM4/OM5) and provides eddy-permitting detail in the ocean while maintaining numerical stability.

## Timestepping and coupling strategy
MOM6 employs a split time-stepping approach, separating fast barotropic (ie, surface gravity wave) modes from slower baraclinic modes ([`SPLIT = True`](https://github.com/ACCESS-NRI/access-om3-configs/blob/408715d5f0a53b105de1ec33cf5676c5d5211ee1/docs/MOM_parameter_doc.all#L4C1-L4C14)). This approach enables stable integration without requiring prohibitively small global timesteps due to fast wave speeds.
- The barotropic mode is sub-cycled within each baroclinic timestep to accommodate the faster dynamics. Key parameters controlling this include:
   - [`DTBT = -0.9`](https://github.com/ACCESS-NRI/access-om3-configs/blob/408715d5f0a53b105de1ec33cf5676c5d5211ee1/docs/MOM_parameter_doc.all#L1580): Automatically computes the barotropic timestep as 90% of the maximum stable value, rounded to a divisor of `DT`. This allows dynamic adaptation to evolving wave speeds (eg, tides) while maintaining stability with minimal sub-cycling.
   - [`DTBT_RESET_PERIOD = 0.0`](https://github.com/ACCESS-NRI/access-om3-configs/blob/408715d5f0a53b105de1ec33cf5676c5d5211ee1/docs/MOM_parameter_doc.all#L101) Resets the barotropic timestep every baroclinic step. This ensures external stability during transient spikes in wave speed, with negligible computational cost at 25km resolution.
   - [`BEBT = 0.20`](https://github.com/ACCESS-NRI/access-om3-configs/blob/408715d5f0a53b105de1ec33cf5676c5d5211ee1/docs/MOM_parameter_doc.all#L1574) Sets the blend between forward-backward (0) and backward Euler (1) time-stepping for barotropic dynamics.
   - [`MAXCFL_BT_CONT`](https://github.com/ACCESS-NRI/access-om3-configs/blob/408715d5f0a53b105de1ec33cf5676c5d5211ee1/docs/MOM_parameter_doc.all#L1558) Limits the instantaneous CFL number for surface-flux corrections, acting as a safeguard against numerical overshoots during extreme events. It remains inactive during normal conditions.

- The baroclinic timstep is set to [`DT = 900.0`](https://github.com/ACCESS-NRI/access-om3-configs/blob/408715d5f0a53b105de1ec33cf5676c5d5211ee1/docs/MOM_parameter_doc.all#L71), chosen to satisfy CFL stability criteria at 25km resolution while balancing throughput. The tracer/thermodynamic timestep is longer at [`DT_THERM = 7200.0`](https://github.com/ACCESS-NRI/access-om3-configs/blob/408715d5f0a53b105de1ec33cf5676c5d5211ee1/docs/MOM_parameter_doc.all#L75), which reduces computational cost by updating slower physics less frequently. We enable [`THERMO_SPANS_COUPLING = True`](https://github.com/ACCESS-NRI/access-om3-configs/blob/408715d5f0a53b105de1ec33cf5676c5d5211ee1/docs/MOM_parameter_doc.all#L80) so that the 2-hour tracer steps can span multiple coupling intervals with the atmosphere. In practice, this means MOM6 will take one thermodynamic step every 2 hours, even though the ocean-ice-atmosphere coupling frequency is higher at [900s](https://github.com/ACCESS-NRI/access-om3-configs/blob/408715d5f0a53b105de1ec33cf5676c5d5211ee1/nuopc.runseq#L2), using the largest integer mutiple of the coupling period. This approach follows common practice in climate models to increase tracer timestep relative to dynamics, improving efficiency while remaining stable.

## Vertical resolution and ALE coordinate
The current configuration uses 75 vertical layers (`NK=75`) with an arbitrary Lagrangian Euler (ALE) vertical coordinate scheme. The ALE scheme is enabled by `USE_REGRIDDING = True` (activating the “split-explicit” layered/reegridding algorithm). Rather than fixed z-levels, MOM6 can operate in a hybrid vertical coordinate mode. The current configuration uses a stretched $z^*$ vertical coordinate `REGRIDDING_COORDINATE_MODE = "ZSTAR"`. The vertical grid spacing is specified via an input file (`ALE_COORDINATE_CONFIG = "FILE:ocean_vgrid.nc,interfaces=zeta"`). The deepest ocean depth is set to `MAXIMUM_DEPTH = 6000.0` and partial bottom cells are effectively used by ALE. Gravitational acceleration (`G_EARTH = 9.8`) and reference density (`RHO_0 = 1035`) are set to standard values, consistent with `BOUSSINESQ = True`. The Boussinesq setup means density variations only affect buoyancy, not total mass, that is the sea level is computed assuming a reference density (here using the fixed reference density for sea-level calc since `CALC_RHO_FOR_SEA_LEVEL = False`).

## Thermodynamics and Equation of State (TEOS-10)
The current configuration uses `EQN_OF_STATE = "ROQUET_RHO"` for seawater, which refers to the polynomial fit of the TEOS-10 equation of state by Roquet et al. (2015). `ROQUET_RHO` uses a 75-term polynomial to compute in-situ density as a function of conservative temperature and absolute salinity (`USE_CONTEMP_ABSSAL = True`), closely approximating the full TEOS-10 results. However, the initial conditions for our configuration use the incorrect pair (ie, conservative temperature vs practical salinity). 

The `_RHO` variant specifically fits density rather than specific volume, ideal for layered models and ensuring that neutral density calculations are precise. The configuration also sets the freezing point formulation to `TFREEZE_FORM = "TEOS_POLY"`, indicating the model computes the seawater freezing temperature with a [TEOS-10](https://www.nco.ncep.noaa.gov/pmb/codes/nwprod/hafs.v2.0.8/sorc/hafs_forecast.fd/MOM6-interface/MOM6/src/equation_of_state/_Equation_of_State.dox#:~:text=This%20one%20or%0ATEOS_poly%20must%20be%20used%20if%20you%20are%20using%20the%20ROQUET_RHO%2C%20ROQUET_SPV%20or%20TEOS%2D10%0Aequation%20of%20state.).

## Surface freezing and salinity constraints
At the ocean surface, we have enabled the realistic sea-ice formation and salinity. We've turned on frazil ice formation (`FRAZIL = TRUE`), which means if the ocean surface layer temperature drops below the freeziing point, the model will convert the negative heat content into frazil ice instead of allowing the water to supercool. By enabling frazil, any heat deficit below freezing in the ocean is passed to the ice component as latent heat of fusion, preventing unrealistically cold liquid water. 

We also ensure salinity never goes negative by setting `BOUND_SALINITY = True`. In coupled models, when sea ice forms or melts, large salinity fluxes occur. This switch prevents numerical issues when the top model cell might be depleted of salt by excessive ice formation. With this parameter on, salinity is clipped at a minimum value (`MIN_SALINITY = 0.0`). If the sea-ice model were to extract more salt than available, the ocean salinity will be floored at 0 and any deficit is ignored, avoiding unphysical negative salinity. In practice, this situation is rare, but it is a safety measure against extreme scenarios (eg, rapid freezing in nearly fresh water). We also set `SALINITY_UNDERFLOW = 0.0`, meaning any tiny salinity values (close to 0) are reset to exactly 0 as well.

Another parameter we adjust is `HFREEZE = 10.0`. This means the model comoputes a "melt potential" over a `10m` layer for sea-ice melt/freeze processes. If `HFREEZE >0`, the ocean will calculate how much heat is available in the top 10 meters to melt ice. 

## Sea surface forcing and boundary conditions
The current configuration is forced with repeating atmospheric conditions and includes weak surface restoring for salinity. We use a repeat-year forcing (RYF) strategy with the JRA55-do dataset. This means the model experiences one year of normal seasonal cycle atmospheric fluxes (wind, heat, precipitation, etc) that is repeated every model year. The advantages are avoiding interannual variability while maintaining a realistic seasonal cycle, helping to equilibrate the ocean state.

### Surface salinity restoring
We use `RESTORE_SALINITY = True` to have sea surface salinity (SSS) is weakly restored to a reference field (`SALT_RESTORE_FILE = "salt_sfc_restore.nc"`), and a piston velocity (`FLUXCONST = 0.11`m/day) is given. The restoring is implemented as a virtual salt flux ( `SRESTORE_AS_SFLUX = True`) to nudge SSS. This approach conserves salt overall (balanced globally by subtracting the mean flux, because we set `ADJUST_NET_SRESTORE_TO_ZERO = True` to avoid altering global salinity). `MAX_DELTA_SRESTORE = 999` hence currently there’s effectively no cap on the SSS anomaly used, more discussions and decisions can be found at [issues/350](https://github.com/ACCESS-NRI/access-om3-configs/issues/350), [issues/325](https://github.com/ACCESS-NRI/access-om3-configs/issues/325), [issues/257](https://github.com/ACCESS-NRI/access-om3-configs/issues/257).

## Diagnostics and tracers
The current configuration intrigers some passive tracers and diagnostics for analysis. For example, we enable `USE_IDEAL_AGE_TRACER = True`, which measures the time since water left the surface. This tracer is incremented by +1 year per year everywhere and reset to 0 at the surface when water is in contact with the atmosphere. It doesn’t affect dynamics but is a diagnostic to understand water mass ventilation and residence times. The cost is minimal, so it was turned on as a useful diagnostic. In the ideal_age module, we also set `DO_IDEAL_AGE = True`.

We also output diagnostics on special vertical coordinates. `NUM_DIAG_COORDS = 2` with `DIAG_COORDS = "z Z ZSTAR", "rho2 RHO2 RHO"`. This means it will produce diagnostics on two sets of vertical levels: one is `Z (depth)` and one is `RHO2`. The settings `DIAG_COORD_DEF_Z = "FILE:ocean_vgrid.nc,interfaces=zeta"` and `DIAG_COORD_DEF_RHO2 = "RFNC1:76,999.5,1020.,1034.1,3.1,1041.,0.002"` indicate how those coordinate surfaces are defined. Finally, the model writes a comprehensive parameter documentation (`DOCUMENT_FILE = "MOM_parameter_doc"` and `COMPLETE_DOCUMENTATION = True`), which is why we have this detailed list attached under `docs` folder. This ensures transparency and reproducibility and all non-default parameters are recorded.

## [MLE Restratification (submesoscale mixing)](https://mom6.readthedocs.io/en/main/api/generated/modules/mom_mixed_layer_restrat.html#:~:text=Mixed%2Dlayer%20eddy,%C2%B6)
This scheme represents the restratification of the mixed layer by submesoscale eddies (`MIXEDLAYER_RESTRAT = True`). It imposes a quasi-Stokes overturning circulation in the mixed layer to counteract deep mixing, helping to restratify the upper ocean after convective events. Enabling MLE restratification prevents unrealistically deep mixed layers and improves surface density structure.

In our configuration, we use [`USE_BODNER23 = True`](https://mom6.readthedocs.io/en/main/api/generated/modules/mom_mixed_layer_restrat.html#:~:text=Bodner%20(2023)%20modification,%C2%B6) which activates Bodner et al. (2023) modified restratification formula. This updated scheme includes a frontal width that depends on the active boundary layer depth and turbulent fluxes. [This scheme needs `MLE_USE_PBL_MLD = True`](https://mom6.readthedocs.io/en/main/api/generated/modules/mom_mixed_layer_restrat.html#:~:text=MLE_USE_PBL_MLD%20must%20be%20True%20to%20use%20the%20B23%20modification.). When using `USE_BODNER23`, a nonzero `CR = 0.0175` (adapted from GFDL) multiplies the eddy streamfunction (it effectively replaces the hard-coded Fox-Kemper $C_e\approx0.0625$ with a tunable value). `BODNER_NSTAR = 0.066` and `BODNER_MSTAR = 0.5` are the respective $n^*$ and $m^*$ in the 
streamfunction. 

## Vertical mixing parameterisations
### Energetic planetary boundary layer (`ePBL`)
The current configuration handles the vertical mixing in the ocean surface boundary layer (`OSBL`) with `ePBL` scheme rather the the traditional `KPP`. The `ePBL` scheme is an energy-based 1D turbulence closure approach that integrates a boundary layer energy budget to determine mixing coefficients. It was developed by Reichl & Hallberg (2018) to improve upon `KPP` for climate simulations by including the effect of `TKE` input and wind-driven mixing in a more physcically constrainted way.

We keep most of paramters in default. Other than that, we incorporate Langmuir turbulence effects - `EPBL_LANGMUIR_SCHEME = “ADDITIVE”`. This choice adds another mixing contribution due to Langmuir circulations (wave-driven mixing), which has been shown to deepen the mixed layer in high wind and wave conditions. Since we do not explicitly couple to a wave model in this configuration (`USE_WAVES = False`), the Langmuir effect is parameterised via a predetermined enhancement factor in `ePBL`. Following GFDL OM5 configuration, we leave the Langmuir enhancement factors at their defaults (eg, `VSTAR_SURF_FAC = 1.2`, `LT_ENHANCE_EXP = –1.5`). This inclusion of wave effects is expected to reduce warm SST biases by enhancing mixing under strong winds, as found in studies of Langmuir turbulence (eg, `USE_LA_LI2016 = True` from Li et al. 2016). The `ePBL` approach overall provides a physically-based estimate of vertical diffusivities constrained by available `TKE`, rather than relying on prescribed profiles as in `KPP`.

For parameters tunning in `ePBL`, we have adjusted some parameters to match the `GFDL` OM4 scheme (`EPBL_MSTAR_SCHEME = “OM4”`). We set `MSTAR_CAP = 1.25` (caps the mixing length scale factor `m` to 1.25) and adjusted coefficients: `MSTAR2_COEF1 = 0.29` and `COEF2 = 0.152`. These tweaks inherited from `GFDL`. We also enable `USE_MLD_ITERATION = True`, which allows `ePBL` to iteratively solve for a self-consistent mixed layer depth (`MLD`) rather than a single-pass estimate. This provides a more accurate `MLD`, especially when multiple criteria (buoyancy, shear) are at play, but at the cost of a few more iterations (`EPBL_MLD_MAX_ITS = 20`). Additionally, we set `EPBL_IS_ADDITIVE = False`, which means that the diffusivity from `ePBL` is not simply added to other sources of diffusivity, instead we let `ePBL` replace shear mixing when it is more energetic, rather than always adding on top. This avoids double counting turbulence. It is a choice that effectively transitions between schemes, for example, in weak wind conditions, shear-driven mixing might dominate, but in strong wind conditions, ePBL mixing dominates.

### Interior shear-driven mixing
Below the surface layer, we use a parameterisation for shear-driven mixing in stratified interior. Specifically we enable the Jackson, Hallberg and Legg (2008) shear instability scheme (`USE_JACKSON_PARAM = True`). This scheme targets mixing in stratified shear zones. It uses a local Richardson number (`Ri`). We keep the critical Richardson number `RINO_CRIT = 0.25` and the nondimensional shear mixing rate `SHEARMIX_RATE = 0.089`. We also set `VERTEX_SHEAR = True`, meaning the shear is computed at cell vertices (horizontally staggered grid) to better capture shear between adjacent grid cells. That is a technical detail to get more accurate shear estimates on a C-grid. The Jackson et al. (2008) parameterisation is energetically constrained hence it iteratively finds a diffusivity such that the energy extracted from the mean flow equals the energy used in mixing plus that lost to dissipation. Our settings allow up to `MAX_RINO_IT = 25` iterations for this solve (inherited from `GFDL`). The Jackson scheme effectively ads interior diffusivity when `Ri<0.25`, gradually reducing it as `Ri` increases beyond critical.

### Internal tidal mixing
`INT_TIDE_DISSIPATION = True` turns on the internal tidal mixing. It activates the parameterisation of internal tidal energy dissipation. We use `INT_TIDE_PROFILE = "POLZIN_09"`, following the tidal energy from Polzin (2009) stretched exponential profile rather than the default St. Laurent exponential. We also set `READ_TIDEAMP = True` with a `tideamp.nc` file and roughness data (`H2_FILE = "bottom_roughness.nc"`). This indicates the model reads spatial maps of tidal velocity amplitude and topographic roughness to inform where internal tides dissipate energy. By doing so, the vertical diffusivity can be enhanced in regions of rough bathymetry and high tidal speeds. `TKE_ITIDE_MAX = 0.1` limits the energy per area can be injected as mixing. Overall, turning on the internal tidal mixing is crucial for simulating the deep ocean stratification and circulation. 

### Interior background mixing
For the ocean interior background mixing, we follow the approach from GFDL of using a weak constant background diapycnal diffusivity ()`KD = 1.5E-05`) for diapycnal mixing. A floor `KD_MIN = 2.0e-6` is also applied, so it won’t go below 2e-6 anywhere, ensuring numerical stability. We enable `DOUBLE_DIFFUSION = True`, which enhances vertical mixing for salt-fingering. Henyey-type internal wave scaling is set through `HENYEY_IGW_BACKGROUND = True`. The parameters `HENYEY_N0_2OMEGA = 20.0` and `HENYEY_MAX_LAT = 73.0` are kept at default. At the same time, to prevent unbounded growth of shear-based or convective mixing, we cap the total diffusivity increment from TKE-based schemes with `KD_MAX = 0.1`. This is a large upper bound that would only be triggered in extremely unstable cases.

The bottom drag is quadratic with coefficient `CDRAG = 0.003`, which is a typical value from ocean observations. `BOTTOMDRAGLAW = True` with `LINEAR_DRAG = False` means a quadratic bottom drag law rather than a linear damping. The thickness of the bottom boundary layer is set to `HBBL = 10.0`.

### Horizontal viscosity and subgrid momentum mixing
In our configuration, we use a hybrid Laplacian-biharmonic viscosity scheme (`LAPLACIAN = True` - 2nd order, `BIHARMONIC = True` - 4th order) to manage unresolved subgrid momentum processes. It helps remove small-scale kinetic energy where it can not resolve it, while preserving large-scale eddy structures. Laplacian viscosity (harmonic) primarily acts on the largest resolved scales, and biharmonic viscosity targets the smaller scales. From the [MOM6 documentation](https://mom6.readthedocs.io/en/main/api/generated/modules/mom_hor_visc.html#namespacemom-hor-visc-1section-horizontal-viscosity:~:text=Laplacian%20viscosity%20coefficient), the harmonic Laplacian viscosity coefficient is computed as following,

$\kappa_{\text{static}} = \min\left[\max\left(\kappa_{\text{bg}}, U_\nu \Delta(x,y), \kappa_{2d}(x,y), \kappa_{\phi}(x,y)\right), \kappa_{max}(x,y)\right]$

where,
1. $\kappa_{\text{bg}}$ (`USE_KH_BG_2D = False`) is constant but spatially variable 2D map, also there is no constant background viscosity (`KH = 0`).
2. $U_\nu \Delta(x,y)$ ($U_\nu$ = `KH_VEL_SCALE = 0.01`) is a constant velocity scale,
3. $\kappa_{\phi}(x,y) = \kappa_\pi|sin(\phi)|^n$ (`KH_SIN_LAT = 2000.0`, `KH_PWR_OF_SINE = 4`) is a function of latitude,

The full viscosity includes the dynamic components,

$\kappa_h(x,y,t) = r(\Delta, L_d)\max\left(\kappa_{\text{static}}, \kappa_{\text{Smagorinsky}}, \kappa_{\text{Leith}}\right)$

where,
1. $r(\Delta, L_d)$ (`RESOLN_SCALED_KH = True`) is a resolution function. This will scale down the Laplacian component of viscosity in well-resolved regions.
2. $\kappa_{\text{Smagorinsky}}$ (`SMAGORINSKY_KH = False`) is from the dynamic Smagorinsky scheme,
3. $\kappa_{\text{Leith}}$ (`LEITH_KH = False`) is the Leith viscosity.

We also enable `BOUND_KH = True` and `BETTER_BOUND_KH = True` to limit the Laplacian coefficient locally to remain CFL stable.

Also, we have `RES_SCALE_MEKE_VISC = False`, meaning we are not scaling MEKE effect on viscosity explicitly. 

With respect to the biharmonic viscosity, we implement a flow-dependent Smagorinsky scheme. There is no background biharmonic viscosity (`AH = 0.0`), while it is dynamically scaled using `SMAGORINSKY_AH = True`, based on the local strain rate. It is controled by `SMAG_BI_CONST = 0.06`, which is the default value of MOM6. We also disable any anisotropic viscosity (`ANISOTROPIC_VISCOSITY = False`). Additionally, the biharmonic coefficient is locally limited to be stable with `BOUND_AH = True` and `BETTER_BOUND_AH = True`.

For the channel drag, a Laplacian Smagorinsky constant ([`SMAG_CONST_CHANNEL = 0.15`](https://github.com/ACCESS-NRI/MOM6/blob/569ba3126835bfcdea5e39c46eeae01938f5413c/src/parameterizations/vertical/MOM_set_viscosity.F90#L967-L969)) is used.

The above combination ensures that strong shear zones (eg, boundary currents, fronts) are damped enough to maintain numerical stability, while allowing relatively unimpeded flow elsewhere.

## Meso-scale eddy parameterisation (isopycnal mixing and GM)
At 25km resolution, the model begins to resolve some mesoscale eddies, but parameterisation is still needed for the unresolved part. The current configuration uses a hybrid parameterisation for mesoscale eddies, combining neutral diffusion (Redi, 1982) and a dynamic GM scheme based on an eddy kinetic energy budget. 

<!-- ### Mesoscale Eddy Kinetic Energy (MEKE)
We use the MEKE scheme (Jansen et al. 2015) to dynamically represent the effect of eddies on tracer transport and momentum. In `MOM6`, `MEKE` is activated by `USE_MEKE = True`. This scheme prognostically calculates a subgrid eddy kinetic energy field and uses it to modulate the eddy diffusivities for tracer mixing and thickness diffusion in space and time. This approach is energy-conserving and resolution-aware, meaning it can smoothly reduce eddy parameterisation strength in regions or at times when actual eddies are resolved. Our configuration does not feed external `EKE` data (`EKE_SOURCE = "prog"`), so the model instability growth provides the source of `EKE`.The scheme then computes an eddy-induced overturning (`GM`) and neutral diffusio (`REDI`) based on this `EKE` and a mixing length. By using `MEKE`, it is ensured that eddy mixing intensifies in energetic regions and diminishes in low-eddy regions or when the grid begins to resolve eddies, thus avoiding the need for a one-size-fits-all eddy diffusivity. 

For the MEKE parameters, we adopt values from GFDL OM5. 
- Setting `MEKE_GMCOEFF = 1` enables the feedback of the MEKE scheme into the `GM` thickness diffusivity, so the eddy energy can now inform the isopycnal thickness diffusion (the GM coefficient). This allows `MEKE` to actively flatten isopycnals in proportion to the EKE, mimicking how real eddies release available potential energy.
- `MEKE_KHMEKE_FAC = 1.0` means the EKE itself can diffuse, which prevents localisation issues by allowing EKE to spread laterally a bit.
- `MEKE_BGSRC = 1.0E-13` prevents EKE from decaying to zero in very quiet regions. It serves as a floor to aid numerical stability and is analogous to a background diffusivity but in energy form.
- `MEKE_KHTH_FAC = 0.5` and `MEKE_KHTR_FAC = 0.5`
- `MEKE_VISCOSITY_COEFF_KU = 1` -->

### Isopycnal thickness diffusion (GM)
`GM` is turned on via `THICKNESSDIFFUSE = True`. Instead of using a fixed GM thickness diffusivity (`KHTH = 0.0`), the Mesoscale Eddy Kinetic Energy (MEKE) scheme (`USE_MEKE = True`) is turned on. MEKE activates a prognostic equation for eddy kinetic energy (EKE) and a spatially varying GM streamfunction. The MEKE parameterisation is based on the work of Jansen et al. (2015), where an EKE budget is solved. The model converts that EKE into an eddy diffusivity (GM diffusivity) via mixing-length theory. In practice, this means the thickness diffusion coefficient is not a fixed number but evolves according to local conditions. Our configuration does not feed external `EKE` data (`EKE_SOURCE = "prog"`), so the model instability growth provides the source of `EKE`. `MEKE_BGSRC = 1.0E-13` prevents EKE from decaying to zero in very quiet regions. It serves as a floor to aid numerical stability and is analogous to a background diffusivity but in energy form. `MEKE_GMCOEFF = 1.0` means the scheme converts eddy potential energy to eddy kinetic energy with 100% efficiency for the GM effect. `MEKE_KHTR_FAC = 0.5` and `MEKE_KHTH_FAC = 0.5` map some of the eddy energy to tracer diffusivity and lateral thickness diffusivity, respectively. So the current configuration actually uses MEKE to the job of GM: flatterning isopycnals to remove available potential energy, but in a physically informed way using a local EKE prognostic variable. We use `KHTH_USE_FGNV_STREAMFUNCTION = True` which solves a 1D boundary value problem so the GM streamfunction is automatically smooth in the vertical and vanishes at the surface and bottom (Ferrari et al., 2010). `FGNV_FILTER_SCALE = 0.1` is used to damp the eddy field noise.

By using MEKE, the model is effectively resolution-aware, as resolution increases and resolves more eddies, the diagnostic EKE and hence GM coefficient naturally reduces. At the same time , in coarser areas or higher latitudes where eddies are still under-resolved, MEKE ramps up the eddy mixing. This avoids the need for ad-hoc spatial maps of GM coefficients. By using `FGNV`, it ensures a robust energetically consistent vertical structure. 

### Isopycnal tracer mixxing
Neutral tracer diffusion is turned on with `USE_NEUTRAL_DIFFUSION = True`, which means tracers are mixed primarily along surfaces of constant density, which greatly reduces spurious diapycnal mixing in stratified oceans. The coefficient for along-isopycnal tracer diffusion is set to `KHTR = 50.0`. This number is adopted from GFDL 0.5 degree configuration. we also use `USE_STORED_SLOPES = True` and keep `NDIFF_CONTINUOUS = True`. 



## Other parameters
1. `INTERPOLATE_P_SURF = False`

MOM6 receives the 2D atmospheric surface pressure field from the coupler at each coupling interval. This parameter controls how MOM6 handles this time-varying field between coupling intervals.
- If it is true, MOM6 interpolates two surface pressure at start ([`p_surf_begin`](https://github.com/ACCESS-NRI/MOM6/blob/569ba3126835bfcdea5e39c46eeae01938f5413c/src/core/MOM.F90#L907C1-L916C12)) and end ([`p_surf_end`](https://github.com/ACCESS-NRI/MOM6/blob/569ba3126835bfcdea5e39c46eeae01938f5413c/src/core/MOM.F90#L907C1-L916C12)) of `step_MOM_dyn` linearly between previous and current values across internal timesteps. The two pressures are then used to calculate `eta_PF_start` (ie, starting $\eta$ for pressure force calculation), which allows `btstep` to split the pressure-forcing term into [an initial component plus a change component](https://github.com/ACCESS-NRI/MOM6/blob/569ba3126835bfcdea5e39c46eeae01938f5413c/src/core/MOM_barotropic.F90#L1034C7-L1035). Then the solver can calculate pressure gradients correctly over time.
- If it is false, MOM6 uses a stepwise constant value throughout the coupling interval.

2. `ADJUST_NET_FRESH_WATER_TO_ZERO = True` and `ADJUST_NET_SRESTORE_TO_ZERO = True`

We set `ADJUST_NET_FRESH_WATER_TO_ZERO = True`, meaning the global net water flux is adjusted to zero each coupling step to avoid drift, and `ADJUST_NET_SRESTORE_TO_ZERO = True` for salt restoring adjustments. These emulate what ACCESS-OM2 did to conserve volume and salt globally. 

3. `OCEAN_SURFACE_STAGGER = "A"` 

This is used in our NUOPC coupler to avoid double interpolation of fields in the mediator. This is a technical detail ensuring that the atmosphere-ocean grid staggering is aligned.






---

The following parameter list was taken from (`access-om3-configs/docs/MOM_parameter_doc.all`):

! This file was written by the model and records all non-layout or debugging parameters used at run-time.

! === module MOM ===
SPLIT = True                    !   [Boolean] default = True
                                ! Use the split time stepping if true.
SPLIT_RK2B = False              !   [Boolean] default = False
                                ! If true, use a version of the split explicit time stepping scheme that
                                ! exchanges velocities with step_MOM that have the average barotropic phase over
                                ! a baroclinic timestep rather than the instantaneous barotropic phase.
CALC_RHO_FOR_SEA_LEVEL = False  !   [Boolean] default = False
                                ! If true, the in-situ density is used to calculate the effective sea level that
                                ! is returned to the coupler. If false, the Boussinesq parameter RHO_0 is used.
ENABLE_THERMODYNAMICS = True    !   [Boolean] default = True
                                ! If true, Temperature and salinity are used as state variables.
USE_EOS = True                  !   [Boolean] default = True
                                ! If true,  density is calculated from temperature and salinity with an equation
                                ! of state.  If USE_EOS is true, ENABLE_THERMODYNAMICS must be true as well.
DIABATIC_FIRST = False          !   [Boolean] default = False
                                ! If true, apply diabatic and thermodynamic processes, including buoyancy
                                ! forcing and mass gain or loss, before stepping the dynamics forward.
USE_CONTEMP_ABSSAL = False      !   [Boolean] default = False
                                ! If true, the prognostics T&S are the conservative temperature and absolute
                                ! salinity. Care should be taken to convert them to potential temperature and
                                ! practical salinity before exchanging them with the coupler and/or reporting
                                ! T&S diagnostics.
ADIABATIC = False               !   [Boolean] default = False
                                ! There are no diapycnal mass fluxes if ADIABATIC is true.  This assumes that KD
                                ! = 0.0 and that there is no buoyancy forcing, but makes the model faster by
                                ! eliminating subroutine calls.
DO_DYNAMICS = True              !   [Boolean] default = True
                                ! If False, skips the dynamics calls that update u & v, as well as the gravity
                                ! wave adjustment to h. This may be a fragile feature, but can be useful during
                                ! development
OFFLINE_TRACER_MODE = False     !   [Boolean] default = False
                                ! If true, barotropic and baroclinic dynamics, thermodynamics are all bypassed
                                ! with all the fields necessary to integrate the tracer advection and diffusion
                                ! equation are read in from files stored from a previous integration of the
                                ! prognostic model. NOTE: This option only used in the ocean_solo_driver.
USE_REGRIDDING = True           !   [Boolean] default = False
                                ! If True, use the ALE algorithm (regridding/remapping). If False, use the
                                ! layered isopycnal algorithm.
REMAP_UV_USING_OLD_ALG = False  !   [Boolean] default = False
                                ! If true, uses the old remapping-via-a-delta-z method for remapping u and v. If
                                ! false, uses the new method that remaps between grids described by an old and
                                ! new thickness.
REMAP_AUXILIARY_VARS = False    !   [Boolean] default = False
                                ! If true, apply ALE remapping to all of the auxiliary 3-dimensional variables
                                ! that are needed to reproduce across restarts, similarly to what is already
                                ! being done with the primary state variables.  The default should be changed to
                                ! true.
BULKMIXEDLAYER = False          !   [Boolean] default = False
                                ! If true, use a Kraus-Turner-like bulk mixed layer with transitional buffer
                                ! layers.  Layers 1 through NKML+NKBL have variable densities. There must be at
                                ! least NKML+NKBL+1 layers if BULKMIXEDLAYER is true. BULKMIXEDLAYER can not be
                                ! used with USE_REGRIDDING. The default is influenced by ENABLE_THERMODYNAMICS.
THICKNESSDIFFUSE = True         !   [Boolean] default = False
                                ! If true, isopycnal surfaces are diffused with a Laplacian coefficient of KHTH.
APPLY_INTERFACE_FILTER = False  !   [Boolean] default = False
                                ! If true, model interface heights are subjected to a grid-scale dependent
                                ! spatial smoothing, often with biharmonic filter.
THICKNESSDIFFUSE_FIRST = True   !   [Boolean] default = False
                                ! If true, do thickness diffusion or interface height smoothing before dynamics.
                                ! This is only used if THICKNESSDIFFUSE or APPLY_INTERFACE_FILTER is true.
USE_POROUS_BARRIER = False      !   [Boolean] default = False
                                ! If true, use porous barrier to constrain the widths and face areas at the
                                ! edges of the grid cells.
BATHYMETRY_AT_VEL = False       !   [Boolean] default = False
                                ! If true, there are separate values for the basin depths at velocity points.
                                ! Otherwise the effects of topography are entirely determined from thickness
                                ! points.
DT = 900.0                      !   [s]
                                ! The (baroclinic) dynamics time step.  The time-step that is actually used will
                                ! be an integer fraction of the forcing time-step (DT_FORCING in ocean-only mode
                                ! or the coupling timestep in coupled mode.)
DT_THERM = 7200.0               !   [s] default = 900.0
                                ! The thermodynamic and tracer advection time step. Ideally DT_THERM should be
                                ! an integer multiple of DT and less than the forcing or coupling time-step,
                                ! unless THERMO_SPANS_COUPLING is true, in which case DT_THERM can be an integer
                                ! multiple of the coupling timestep.  By default DT_THERM is set to DT.
THERMO_SPANS_COUPLING = True    !   [Boolean] default = False
                                ! If true, the MOM will take thermodynamic and tracer timesteps that can be
                                ! longer than the coupling timestep. The actual thermodynamic timestep that is
                                ! used in this case is the largest integer multiple of the coupling timestep
                                ! that is less than or equal to DT_THERM.
HMIX_SFC_PROP = 1.0             !   [m] default = 1.0
                                ! If BULKMIXEDLAYER is false, HMIX_SFC_PROP is the depth over which to average
                                ! to find surface properties like SST and SSS or density (but not surface
                                ! velocities).
HMIX_UV_SFC_PROP = 0.0          !   [m] default = 0.0
                                ! If BULKMIXEDLAYER is false, HMIX_UV_SFC_PROP is the depth over which to
                                ! average to find surface flow properties, SSU, SSV. A non-positive value
                                ! indicates no averaging.
HFREEZE = 10.0                  !   [m] default = -1.0
                                ! If HFREEZE > 0, melt potential will be computed. The actual depth over which
                                ! melt potential is computed will be min(HFREEZE, OBLD), where OBLD is the
                                ! boundary layer depth. If HFREEZE <= 0 (default), melt potential will not be
                                ! computed.
INTERPOLATE_P_SURF = False      !   [Boolean] default = False
                                ! If true, linearly interpolate the surface pressure over the coupling time
                                ! step, using the specified value at the end of the step.
DTBT_RESET_PERIOD = 0.0         !   [s] default = 7200.0
                                ! The period between recalculations of DTBT (if DTBT <= 0). If DTBT_RESET_PERIOD
                                ! is negative, DTBT is set based only on information available at
                                ! initialization.  If 0, DTBT will be set every dynamics time step. The default
                                ! is set by DT_THERM.  This is only used if SPLIT is true.
FRAZIL = True                   !   [Boolean] default = False
                                ! If true, water freezes if it gets too cold, and the accumulated heat deficit
                                ! is returned in the surface state.  FRAZIL is only used if
                                ! ENABLE_THERMODYNAMICS is true.
DO_GEOTHERMAL = False           !   [Boolean] default = False
                                ! If true, apply geothermal heating.
BOUND_SALINITY = True           !   [Boolean] default = False
                                ! If true, limit salinity to being positive. (The sea-ice model may ask for more
                                ! salt than is available and drive the salinity negative otherwise.)
MIN_SALINITY = 0.0              !   [PPT] default = 0.0
                                ! The minimum value of salinity when BOUND_SALINITY=True.
SALINITY_UNDERFLOW = 0.0        !   [PPT] default = 0.0
                                ! A tiny value of salinity below which the it is set to 0.  For reference, one
                                ! molecule of salt per square meter of ocean is of order 1e-29 ppt.
TEMPERATURE_UNDERFLOW = 0.0     !   [degC] default = 0.0
                                ! A tiny magnitude of temperatures below which they are set to 0.
C_P = 3992.0                    !   [J kg-1 K-1] default = 3991.86795711963
                                ! The heat capacity of sea water, approximated as a constant. This is only used
                                ! if ENABLE_THERMODYNAMICS is true. The default value is from the TEOS-10
                                ! definition of conservative temperature.
USE_PSURF_IN_EOS = False        !   [Boolean] default = True
                                ! If true, always include the surface pressure contributions in equation of
                                ! state calculations.
P_REF = 2.0E+07                 !   [Pa] default = 2.0E+07
                                ! The pressure that is used for calculating the coordinate density.  (1 Pa = 1e4
                                ! dbar, so 2e7 is commonly used.) This is only used if USE_EOS and
                                ! ENABLE_THERMODYNAMICS are true.
FIRST_DIRECTION = 0             ! default = 0
                                ! An integer that indicates which direction goes first in parts of the code that
                                ! use directionally split updates, with even numbers (or 0) used for x- first
                                ! and odd numbers used for y-first.
ALTERNATE_FIRST_DIRECTION = False !   [Boolean] default = False
                                ! If true, after every dynamic timestep alternate whether the x- or y- direction
                                ! updates occur first in directionally split parts of the calculation. If this
                                ! is true, FIRST_DIRECTION applies at the start of a new run or if the next
                                ! first direction can not be found in the restart file.
CHECK_BAD_SURFACE_VALS = True   !   [Boolean] default = False
                                ! If true, check the surface state for ridiculous values.
BAD_VAL_SSH_MAX = 50.0          !   [m] default = 20.0
                                ! The value of SSH above which a bad value message is triggered, if
                                ! CHECK_BAD_SURFACE_VALS is true.
BAD_VAL_SSS_MAX = 75.0          !   [PPT] default = 45.0
                                ! The value of SSS above which a bad value message is triggered, if
                                ! CHECK_BAD_SURFACE_VALS is true.
BAD_VAL_SST_MAX = 55.0          !   [deg C] default = 45.0
                                ! The value of SST above which a bad value message is triggered, if
                                ! CHECK_BAD_SURFACE_VALS is true.
BAD_VAL_SST_MIN = -3.0          !   [deg C] default = -2.1
                                ! The value of SST below which a bad value message is triggered, if
                                ! CHECK_BAD_SURFACE_VALS is true.
BAD_VAL_COLUMN_THICKNESS = 0.0  !   [m] default = 0.0
                                ! The value of column thickness below which a bad value message is triggered, if
                                ! CHECK_BAD_SURFACE_VALS is true.
DEFAULT_ANSWER_DATE = 99991231  ! default = 99991231
                                ! This sets the default value for the various _ANSWER_DATE parameters.
SURFACE_ANSWER_DATE = 99991231  ! default = 99991231
                                ! The vintage of the expressions for the surface properties.  Values below
                                ! 20190101 recover the answers from the end of 2018, while higher values use
                                ! updated and more robust forms of the same expressions.
USE_DIABATIC_TIME_BUG = False   !   [Boolean] default = False
                                ! If true, uses the wrong calendar time for diabatic processes, as was done in
                                ! MOM6 versions prior to February 2018. This is not recommended.
SAVE_INITIAL_CONDS = True       !   [Boolean] default = False
                                ! If true, write the initial conditions to a file given by IC_OUTPUT_FILE.
IC_OUTPUT_FILE = "MOM_IC"       ! default = "MOM_IC"
                                ! The file into which to write the initial conditions.
WRITE_GEOM = 1                  ! default = 1
                                ! If =0, never write the geometry and vertical grid files. If =1, write the
                                ! geometry and vertical grid files only for a new simulation. If =2, always
                                ! write the geometry and vertical grid files. Other values are invalid.
USE_DBCLIENT = False            !   [Boolean] default = False
                                ! If true, initialize a client to a remote database that can be used for online
                                ! analysis and machine-learning inference.
USE_PARTICLES = False           !   [Boolean] default = False
                                ! If true, use the particles package.
USE_UH_PARTICLES = False        !   [Boolean] default = False
                                ! If true, use the uh velocity in the particles package.
ENSEMBLE_OCEAN = False          !   [Boolean] default = False
                                ! If False, The model is being run in serial mode as a single realization. If
                                ! True, The current model realization is part of a larger ensemble and at the
                                ! end of step MOM, we will perform a gather of the ensemble members for
                                ! statistical evaluation and/or data assimilation.
HOMOGENIZE_FORCINGS = False     !   [Boolean] default = False
                                ! If True, homogenize the forces and fluxes.

! === module MOM_domains ===
REENTRANT_X = True              !   [Boolean] default = True
                                ! If true, the domain is zonally reentrant.
REENTRANT_Y = False             !   [Boolean] default = False
                                ! If true, the domain is meridionally reentrant.
TRIPOLAR_N = True               !   [Boolean] default = False
                                ! Use tripolar connectivity at the northern edge of the domain.  With
                                ! TRIPOLAR_N, NIGLOBAL must be even.
NIGLOBAL = 1440                 !
                                ! The total number of thickness grid points in the x-direction in the physical
                                ! domain. With STATIC_MEMORY_ this is set in MOM_memory.h at compile time.
NJGLOBAL = 1142                 !
                                ! The total number of thickness grid points in the y-direction in the physical
                                ! domain. With STATIC_MEMORY_ this is set in MOM_memory.h at compile time.
NIHALO = 4                      ! default = 4
                                ! The number of halo points on each side in the x-direction.  How this is set
                                ! varies with the calling component and static or dynamic memory configuration.
NJHALO = 4                      ! default = 4
                                ! The number of halo points on each side in the y-direction.  How this is set
                                ! varies with the calling component and static or dynamic memory configuration.

! === module MOM_hor_index ===
! Sets the horizontal array index types.

! === module MOM_grid ===
! Parameters providing information about the lateral grid.
REFERENCE_HEIGHT = 0.0          !   [m] default = 0.0
                                ! A reference value for geometric height fields, such as bathyT.

! === module MOM_fixed_initialization ===
INPUTDIR = "./INPUT/"           ! default = "."
                                ! The directory in which input files are found.

! === module MOM_grid_init ===
GRID_CONFIG = "mosaic"          !
                                ! A character string that determines the method for defining the horizontal
                                ! grid.  Current options are:
                                !     mosaic - read the grid from a mosaic (supergrid)
                                !              file set by GRID_FILE.
                                !     cartesian - use a (flat) Cartesian grid.
                                !     spherical - use a simple spherical grid.
                                !     mercator - use a Mercator spherical grid.
GRID_FILE = "ocean_hgrid.nc"    !
                                ! Name of the file from which to read horizontal grid data.
USE_TRIPOLAR_GEOLONB_BUG = False !   [Boolean] default = False
                                ! If true, use older code that incorrectly sets the longitude in some points
                                ! along the tripolar fold to be off by 360 degrees.
RAD_EARTH = 6.371229E+06        !   [m] default = 6.378E+06
                                ! The radius of the Earth.
TOPO_CONFIG = "file"            !
                                ! This specifies how bathymetry is specified:
                                !     file - read bathymetric information from the file
                                !       specified by (TOPO_FILE).
                                !     flat - flat bottom set to MAXIMUM_DEPTH.
                                !     bowl - an analytically specified bowl-shaped basin
                                !       ranging between MAXIMUM_DEPTH and MINIMUM_DEPTH.
                                !     spoon - a similar shape to 'bowl', but with an vertical
                                !       wall at the southern face.
                                !     halfpipe - a zonally uniform channel with a half-sine
                                !       profile in the meridional direction.
                                !     bbuilder - build topography from list of functions.
                                !     benchmark - use the benchmark test case topography.
                                !     Neverworld - use the Neverworld test case topography.
                                !     DOME - use a slope and channel configuration for the
                                !       DOME sill-overflow test case.
                                !     ISOMIP - use a slope and channel configuration for the
                                !       ISOMIP test case.
                                !     DOME2D - use a shelf and slope configuration for the
                                !       DOME2D gravity current/overflow test case.
                                !     Kelvin - flat but with rotated land mask.
                                !     seamount - Gaussian bump for spontaneous motion test case.
                                !     dumbbell - Sloshing channel with reservoirs on both ends.
                                !     shelfwave - exponential slope for shelfwave test case.
                                !     Phillips - ACC-like idealized topography used in the Phillips config.
                                !     dense - Denmark Strait-like dense water formation and overflow.
                                !     USER - call a user modified routine.
TOPO_FILE = "topog.nc"          ! default = "topog.nc"
                                ! The file from which the bathymetry is read.
TOPO_VARNAME = "depth"          ! default = "depth"
                                ! The name of the bathymetry variable in TOPO_FILE.
TOPO_EDITS_FILE = ""            ! default = ""
                                ! The file from which to read a list of i,j,z topography overrides.
ALLOW_LANDMASK_CHANGES = False  !   [Boolean] default = False
                                ! If true, allow topography overrides to change land mask.
MINIMUM_DEPTH = 0.0             !   [m] default = 0.0
                                ! If MASKING_DEPTH is unspecified, then anything shallower than MINIMUM_DEPTH is
                                ! assumed to be land and all fluxes are masked out. If MASKING_DEPTH is
                                ! specified, then all depths shallower than MINIMUM_DEPTH but deeper than
                                ! MASKING_DEPTH are rounded to MINIMUM_DEPTH.
MASKING_DEPTH = -9999.0         !   [m] default = -9999.0
                                ! The depth below which to mask points as land points, for which all fluxes are
                                ! zeroed out. MASKING_DEPTH is ignored if it has the special default value.
MAXIMUM_DEPTH = 6000.0          !   [m]
                                ! The maximum depth of the ocean.

! === module MOM_open_boundary ===
! Controls where open boundaries are located, what kind of boundary condition to impose, and what data to apply,
! if any.
OBC_NUMBER_OF_SEGMENTS = 0      ! default = 0
                                ! The number of open boundary segments.
CHANNEL_CONFIG = "none"         ! default = "none"
                                ! A parameter that determines which set of channels are
                                ! restricted to specific  widths.  Options are:
                                !     none - All channels have the grid width.
                                !     global_1deg - Sets 16 specific channels appropriate
                                !       for a 1-degree model, as used in CM2G.
                                !     list - Read the channel locations and widths from a
                                !       text file, like MOM_channel_list in the MOM_SIS
                                !       test case.
                                !     file - Read open face widths everywhere from a
                                !       NetCDF file on the model grid.
SUBGRID_TOPO_AT_VEL = False     !   [Boolean] default = False
                                ! If true, use variables from TOPO_AT_VEL_FILE as parameters for porous barrier.
ROTATION = "2omegasinlat"       ! default = "2omegasinlat"
                                ! This specifies how the Coriolis parameter is specified:
                                !     2omegasinlat - Use twice the planetary rotation rate
                                !       times the sine of latitude.
                                !     betaplane - Use a beta-plane or f-plane.
                                !     USER - call a user modified routine.
OMEGA = 7.2921E-05              !   [s-1] default = 7.2921E-05
                                ! The rotation rate of the earth.
GRID_ROTATION_ANGLE_BUGS = False !   [Boolean] default = False
                                ! If true, use an older algorithm to calculate the sine and cosines needed
                                ! rotate between grid-oriented directions and true north and east.  Differences
                                ! arise at the tripolar fold.

! === module MOM_verticalGrid ===
! Parameters providing information about the vertical grid.
G_EARTH = 9.8                   !   [m s-2] default = 9.8
                                ! The gravitational acceleration of the Earth.
RHO_0 = 1035.0                  !   [kg m-3] default = 1035.0
                                ! The mean ocean density used with BOUSSINESQ true to calculate accelerations
                                ! and the mass for conservation properties, or with BOUSSINSEQ false to convert
                                ! some parameters from vertical units of m to kg m-2.
BOUSSINESQ = True               !   [Boolean] default = True
                                ! If true, make the Boussinesq approximation.
ANGSTROM = 1.0E-10              !   [m] default = 1.0E-10
                                ! The minimum layer thickness, usually one-Angstrom.
H_TO_M = 1.0                    !   [m H-1] default = 1.0
                                ! A constant that translates the model's internal units of thickness into m.
NK = 75                         !   [nondim]
                                ! The number of model layers.

! === module MOM_tracer_registry ===

! === module MOM_EOS ===
EQN_OF_STATE = "WRIGHT_REDUCED" ! default = "WRIGHT"
                                ! EQN_OF_STATE determines which ocean equation of state should be used.
                                ! Currently, the valid choices are "LINEAR", "UNESCO", "JACKETT_MCD", "WRIGHT",
                                ! "WRIGHT_REDUCED", "WRIGHT_FULL", "NEMO", "ROQUET_RHO", "ROQUET_SPV" and
                                ! "TEOS10".  This is only used if USE_EOS is true.
EOS_QUADRATURE = False          !   [Boolean] default = False
                                ! If true, always use the generic (quadrature) code code for the integrals of
                                ! density.
TFREEZE_FORM = "LINEAR"         ! default = "LINEAR"
                                ! TFREEZE_FORM determines which expression should be used for the freezing
                                ! point.  Currently, the valid choices are "LINEAR", "MILLERO_78", "TEOS_POLY",
                                ! "TEOS10"
TFREEZE_S0_P0 = 0.0             !   [degC] default = 0.0
                                ! When TFREEZE_FORM=LINEAR, this is the freezing potential temperature at S=0,
                                ! P=0.
DTFREEZE_DS = -0.054            !   [degC ppt-1] default = -0.054
                                ! When TFREEZE_FORM=LINEAR, this is the derivative of the freezing potential
                                ! temperature with salinity.
DTFREEZE_DP = -7.75E-08         !   [degC Pa-1] default = 0.0
                                ! When TFREEZE_FORM=LINEAR, this is the derivative of the freezing potential
                                ! temperature with pressure.

! === module MOM_restart ===
PARALLEL_RESTARTFILES = False   !   [Boolean] default = False
                                ! If true, the IO layout is used to group processors that write to the same
                                ! restart file or each processor writes its own (numbered) restart file. If
                                ! false, a single restart file is generated combining output from all PEs.
RESTARTFILE = "MOM.res"         ! default = "MOM.res"
                                ! The name-root of the restart file.
MAX_FIELDS = 100                ! default = 100
                                ! The maximum number of restart fields that can be used.
RESTART_CHECKSUMS_REQUIRED = True !   [Boolean] default = True
                                ! If true, require the restart checksums to match and error out otherwise. Users
                                ! may want to avoid this comparison if for example the restarts are made from a
                                ! run with a different mask_table than the current run, in which case the
                                ! checksums will not match and cause crash.
STREAMING_FILTER_M2 = False     !   [Boolean] default = False
                                ! If true, turn on streaming band-pass filter for detecting instantaneous tidal
                                ! signals.
STREAMING_FILTER_K1 = False     !   [Boolean] default = False
                                ! If true, turn on streaming band-pass filter for detecting instantaneous tidal
                                ! signals.

! === module MOM_tracer_flow_control ===
USE_USER_TRACER_EXAMPLE = False !   [Boolean] default = False
                                ! If true, use the USER_tracer_example tracer package.
USE_DOME_TRACER = False         !   [Boolean] default = False
                                ! If true, use the DOME_tracer tracer package.
USE_ISOMIP_TRACER = False       !   [Boolean] default = False
                                ! If true, use the ISOMIP_tracer tracer package.
USE_RGC_TRACER = False          !   [Boolean] default = False
                                ! If true, use the RGC_tracer tracer package.
USE_IDEAL_AGE_TRACER = True     !   [Boolean] default = False
                                ! If true, use the ideal_age_example tracer package.
USE_REGIONAL_DYES = False       !   [Boolean] default = False
                                ! If true, use the regional_dyes tracer package.
USE_OIL_TRACER = False          !   [Boolean] default = False
                                ! If true, use the oil_tracer tracer package.
USE_ADVECTION_TEST_TRACER = False !   [Boolean] default = False
                                ! If true, use the advection_test_tracer tracer package.
USE_OCMIP2_CFC = False          !   [Boolean] default = False
                                ! If true, use the MOM_OCMIP2_CFC tracer package.
USE_CFC_CAP = False             !   [Boolean] default = False
                                ! If true, use the MOM_CFC_cap tracer package.
USE_generic_tracer = False      !   [Boolean] default = False
                                ! If true and _USE_GENERIC_TRACER is defined as a preprocessor macro, use the
                                ! MOM_generic_tracer packages.
USE_PSEUDO_SALT_TRACER = False  !   [Boolean] default = False
                                ! If true, use the pseudo salt tracer, typically run as a diagnostic.
USE_BOUNDARY_IMPULSE_TRACER = False !   [Boolean] default = False
                                ! If true, use the boundary impulse tracer.
USE_DYED_OBC_TRACER = False     !   [Boolean] default = False
                                ! If true, use the dyed_obc_tracer tracer package.
USE_NW2_TRACERS = False         !   [Boolean] default = False
                                ! If true, use the NeverWorld2 tracers.

! === module ideal_age_example ===
DO_IDEAL_AGE = True             !   [Boolean] default = True
                                ! If true, use an ideal age tracer that is set to 0 age in the boundary layer
                                ! and ages at unit rate in the interior.
DO_IDEAL_VINTAGE = False        !   [Boolean] default = False
                                ! If true, use an ideal vintage tracer that is set to an exponentially
                                ! increasing value in the boundary layer and is conserved thereafter.
DO_IDEAL_AGE_DATED = False      !   [Boolean] default = False
                                ! If true, use an ideal age tracer that is everywhere 0 before
                                ! IDEAL_AGE_DATED_START_YEAR, but the behaves like the standard ideal age tracer
                                ! - i.e. is set to 0 age in the boundary layer and ages at unit rate in the
                                ! interior.
DO_BL_RESIDENCE = False         !   [Boolean] default = False
                                ! If true, use a residence tracer that is set to 0 age in the interior and ages
                                ! at unit rate in the boundary layer.
USE_REAL_BL_DEPTH = False       !   [Boolean] default = False
                                ! If true, the ideal age tracers will use the boundary layer depth diagnosed
                                ! from the BL or bulkmixedlayer scheme.
AGE_IC_FILE = ""                ! default = ""
                                ! The file in which the age-tracer initial values can be found, or an empty
                                ! string for internal initialization.
AGE_IC_FILE_IS_Z = False        !   [Boolean] default = False
                                ! If true, AGE_IC_FILE is in depth space, not layer space
TRACERS_MAY_REINIT = False      !   [Boolean] default = False
                                ! If true, tracers may go through the initialization code if they are not found
                                ! in the restart files.  Otherwise it is a fatal error if the tracers are not
                                ! found in the restart files of a restarted run.

! === module MOM_coord_initialization ===
COORD_CONFIG = "none"           ! default = "none"
                                ! This specifies how layers are to be defined:
                                !     ALE or none - used to avoid defining layers in ALE mode
                                !     file - read coordinate information from the file
                                !       specified by (COORD_FILE).
                                !     BFB - Custom coords for buoyancy-forced basin case
                                !       based on SST_S, T_BOT and DRHO_DT.
                                !     linear - linear based on interfaces not layers
                                !     layer_ref - linear based on layer densities
                                !     ts_ref - use reference temperature and salinity
                                !     ts_range - use range of temperature and salinity
                                !       (T_REF and S_REF) to determine surface density
                                !       and GINT calculate internal densities.
                                !     gprime - use reference density (RHO_0) for surface
                                !       density and GINT calculate internal densities.
                                !     ts_profile - use temperature and salinity profiles
                                !       (read from COORD_FILE) to set layer densities.
                                !     USER - call a user modified routine.
GFS = 9.8                       !   [m s-2] default = 9.8
                                ! The reduced gravity at the free surface.
LIGHTEST_DENSITY = 1035.0       !   [kg m-3] default = 1035.0
                                ! The reference potential density used for layer 1.
REGRIDDING_COORDINATE_MODE = "ZSTAR" ! default = "LAYER"
                                ! Coordinate mode for vertical regridding. Choose among the following
                                ! possibilities:  LAYER - Isopycnal or stacked shallow water layers
                                !  ZSTAR, Z* - stretched geopotential z*
                                !  SIGMA_SHELF_ZSTAR - stretched geopotential z* ignoring shelf
                                !  SIGMA - terrain following coordinates
                                !  RHO   - continuous isopycnal
                                !  HYCOM1 - HyCOM-like hybrid coordinate
                                !  HYBGEN - Hybrid coordinate from the Hycom hybgen code
                                !  ADAPTIVE - optimize for smooth neutral density surfaces
REGRIDDING_COORDINATE_UNITS = "m" ! default = "m"
                                ! Units of the regridding coordinate.
ALE_COORDINATE_CONFIG = "FILE:ocean_vgrid.nc,interfaces=zeta" ! default = "UNIFORM"
                                ! Determines how to specify the coordinate resolution. Valid options are:
                                !  PARAM       - use the vector-parameter ALE_RESOLUTION
                                !  UNIFORM[:N] - uniformly distributed
                                !  FILE:string - read from a file. The string specifies
                                !                the filename and variable name, separated
                                !                by a comma or space, e.g. FILE:lev.nc,dz
                                !                or FILE:lev.nc,interfaces=zw
                                !  WOA09[:N]   - the WOA09 vertical grid (approximately)
                                !  WOA09INT[:N] - layers spanned by the WOA09 depths
                                !  WOA23INT[:N] - layers spanned by the WOA23 depths
                                !  FNC1:string - FNC1:dz_min,H_total,power,precision
                                !  HYBRID:string - read from a file. The string specifies
                                !                the filename and two variable names, separated
                                !                by a comma or space, for sigma-2 and dz. e.g.
                                !                HYBRID:vgrid.nc,sigma2,dz
!ALE_RESOLUTION = 1.0825614929199219, 1.1963462829589844, 1.322089672088623, 1.4610481262207031, 1.614609718322754, 1.784308910369873, 1.9718408584594727, 2.1790781021118164, 2.4080896377563477, 2.661160469055176, 2.940814971923828, 3.249845504760742, 3.591329574584961, 3.968667984008789, 4.385614395141602, 4.846321105957031, 5.355350494384766, 5.917766571044922, 6.539115905761719, 7.225547790527344, 7.983818054199219, 8.821372985839844, 9.746376037597656, 10.767845153808594, 11.895652770996094, 13.140586853027344, 14.514511108398438, 16.030319213867188, 17.7020263671875, 19.544876098632812, 21.575271606445312, 23.810821533203125, 26.270294189453125, 28.973419189453125, 31.94091796875, 35.194000244140625, 38.75390625, 42.641632080078125, 46.876739501953125, 51.476593017578125, 56.45489501953125, 61.82025146484375, 67.5743408203125, 73.70965576171875, 80.207763671875, 87.03759765625, 94.1534423828125, 101.4951171875, 108.9879150390625, 116.5452880859375, 124.0714111328125, 131.4671630859375, 138.6346435546875, 145.484130859375, 151.938232421875, 157.93701171875, 163.439697265625, 168.42431640625, 172.8876953125, 176.842041015625, 180.3125, 183.33154296875, 185.938720703125, 188.175048828125, 190.08251953125, 191.701171875
MIN_THICKNESS = 0.001           !   [m] default = 0.001
                                ! When regridding, this is the minimum layer thickness allowed.
REMAPPING_SCHEME = "PPM_H4"     ! default = "PLM"
                                ! This sets the reconstruction scheme used for vertical remapping for all
                                ! variables. It can be one of the following schemes:
                                ! PCM         (1st-order accurate)
                                ! PLM         (2nd-order accurate)
                                ! PLM_HYBGEN  (2nd-order accurate)
                                ! PPM_H4      (3rd-order accurate)
                                ! PPM_IH4     (3rd-order accurate)
                                ! PPM_HYBGEN  (3rd-order accurate)
                                ! WENO_HYBGEN (3rd-order accurate)
                                ! PQM_IH4IH3  (4th-order accurate)
                                ! PQM_IH6IH5  (5th-order accurate)
VELOCITY_REMAPPING_SCHEME = "PPM_H4" ! default = "PPM_H4"
                                ! This sets the reconstruction scheme used for vertical remapping of velocities.
                                ! By default it is the same as REMAPPING_SCHEME. It can be one of the following
                                ! schemes:
                                ! PCM         (1st-order accurate)
                                ! PLM         (2nd-order accurate)
                                ! PLM_HYBGEN  (2nd-order accurate)
                                ! PPM_H4      (3rd-order accurate)
                                ! PPM_IH4     (3rd-order accurate)
                                ! PPM_HYBGEN  (3rd-order accurate)
                                ! WENO_HYBGEN (3rd-order accurate)
                                ! PQM_IH4IH3  (4th-order accurate)
                                ! PQM_IH6IH5  (5th-order accurate)
FATAL_CHECK_RECONSTRUCTIONS = False !   [Boolean] default = False
                                ! If true, cell-by-cell reconstructions are checked for consistency and if
                                ! non-monotonicity or an inconsistency is detected then a FATAL error is issued.
FATAL_CHECK_REMAPPING = False   !   [Boolean] default = False
                                ! If true, the results of remapping are checked for conservation and new extrema
                                ! and if an inconsistency is detected then a FATAL error is issued.
REMAP_BOUND_INTERMEDIATE_VALUES = False !   [Boolean] default = False
                                ! If true, the values on the intermediate grid used for remapping are forced to
                                ! be bounded, which might not be the case due to round off.
REMAP_BOUNDARY_EXTRAP = False   !   [Boolean] default = False
                                ! If true, values at the interfaces of boundary cells are extrapolated instead
                                ! of piecewise constant
INIT_BOUNDARY_EXTRAP = False    !   [Boolean] default = False
                                ! If true, values at the interfaces of boundary cells are extrapolated instead
                                ! of piecewise constant during initialization.Defaults to REMAP_BOUNDARY_EXTRAP.
REMAPPING_USE_OM4_SUBCELLS = False !   [Boolean] default = True
                                ! This selects the remapping algorithm used in OM4 that does not use the full
                                ! reconstruction for the top- and lower-most sub-layers, but instead assumes
                                ! they are always vanished (untrue) and so just uses their edge values. We
                                ! recommend setting this option to false.
REMAPPING_ANSWER_DATE = 99991231 ! default = 99991231
                                ! The vintage of the expressions and order of arithmetic to use for remapping.
                                ! Values below 20190101 result in the use of older, less accurate expressions
                                ! that were in use at the end of 2018.  Higher values result in the use of more
                                ! robust and accurate forms of mathematically equivalent expressions.
PARTIAL_CELL_VELOCITY_REMAP = False !   [Boolean] default = False
                                ! If true, use partial cell thicknesses at velocity points that are masked out
                                ! where they extend below the shallower of the neighboring bathymetry for
                                ! remapping velocity.
REMAP_AFTER_INITIALIZATION = True !   [Boolean] default = True
                                ! If true, applies regridding and remapping immediately after initialization so
                                ! that the state is ALE consistent. This is a legacy step and should not be
                                ! needed if the initialization is consistent with the coordinate mode.
REGRID_TIME_SCALE = 0.0         !   [s] default = 0.0
                                ! The time-scale used in blending between the current (old) grid and the target
                                ! (new) grid. A short time-scale favors the target grid (0. or anything less
                                ! than DT_THERM) has no memory of the old grid. A very long time-scale makes the
                                ! model more Lagrangian.
REGRID_FILTER_SHALLOW_DEPTH = 0.0 !   [m] default = 0.0
                                ! The depth above which no time-filtering is applied. Above this depth final
                                ! grid exactly matches the target (new) grid.
REGRID_FILTER_DEEP_DEPTH = 0.0  !   [m] default = 0.0
                                ! The depth below which full time-filtering is applied with time-scale
                                ! REGRID_TIME_SCALE. Between depths REGRID_FILTER_SHALLOW_DEPTH and
                                ! REGRID_FILTER_SHALLOW_DEPTH the filter weights adopt a cubic profile.
REMAP_VEL_MASK_BBL_THICK = -0.001 !   [m] default = -0.001
                                ! A thickness of a bottom boundary layer below which velocities in thin layers
                                ! are zeroed out after remapping, following practice with Hybgen remapping, or a
                                ! negative value to avoid such filtering altogether.

! === module MOM_state_initialization ===
FATAL_INCONSISTENT_RESTART_TIME = False !   [Boolean] default = False
                                ! If true and a time_in value is provided to MOM_initialize_state, verify that
                                ! the time read from a restart file is the same as time_in, and issue a fatal
                                ! error if it is not.  Otherwise, simply set the time to time_in if present.
INIT_LAYERS_FROM_Z_FILE = True  !   [Boolean] default = False
                                ! If true, initialize the layer thicknesses, temperatures, and salinities from a
                                ! Z-space file on a latitude-longitude grid.

! === module MOM_initialize_layers_from_Z ===
TEMP_SALT_Z_INIT_FILE = "ocean_temp_salt.res.nc" ! default = "temp_salt_z.nc"
                                ! The name of the z-space input file used to initialize temperatures (T) and
                                ! salinities (S). If T and S are not in the same file, TEMP_Z_INIT_FILE and
                                ! SALT_Z_INIT_FILE must be set.
TEMP_Z_INIT_FILE = "ocean_temp_salt.res.nc" ! default = "ocean_temp_salt.res.nc"
                                ! The name of the z-space input file used to initialize temperatures, only.
SALT_Z_INIT_FILE = "ocean_temp_salt.res.nc" ! default = "ocean_temp_salt.res.nc"
                                ! The name of the z-space input file used to initialize temperatures, only.
Z_INIT_FILE_PTEMP_VAR = "temp"  ! default = "ptemp"
                                ! The name of the potential temperature variable in TEMP_Z_INIT_FILE.
Z_INIT_FILE_SALT_VAR = "salt"   ! default = "salt"
                                ! The name of the salinity variable in SALT_Z_INIT_FILE.
Z_INIT_HOMOGENIZE = False       !   [Boolean] default = False
                                ! If True, then horizontally homogenize the interpolated initial conditions.
Z_INIT_ALE_REMAPPING = True     !   [Boolean] default = False
                                ! If True, then remap straight to model coordinate from file.
Z_INIT_REMAPPING_SCHEME = "PPM_IH4" ! default = "PPM_IH4"
                                ! The remapping scheme to use if using Z_INIT_ALE_REMAPPING is True.
Z_INIT_REMAP_GENERAL = True     !   [Boolean] default = False
                                ! If false, only initializes to z* coordinates. If true, allows initialization
                                ! directly to general coordinates.
Z_INIT_REMAP_FULL_COLUMN = True !   [Boolean] default = True
                                ! If false, only reconstructs profiles for valid data points. If true, inserts
                                ! vanished layers below the valid data.
Z_INIT_REMAP_OLD_ALG = False    !   [Boolean] default = False
                                ! If false, uses the preferred remapping algorithm for initialization. If true,
                                ! use an older, less robust algorithm for remapping.
TEMP_SALT_INIT_VERTICAL_REMAP_ONLY = True !   [Boolean] default = False
                                ! If true, initial conditions are on the model horizontal grid. Extrapolation
                                ! over missing ocean values is done using an ICE-9 procedure with vertical ALE
                                ! remapping .
Z_INIT_REMAPPING_USE_OM4_SUBCELLS = False !   [Boolean] default = True
                                ! If true, use the OM4 remapping-via-subcells algorithm for initialization. See
                                ! REMAPPING_USE_OM4_SUBCELLS for more details. We recommend setting this option
                                ! to false.
HOR_REGRID_ANSWER_DATE = 99991231 ! default = 99991231
                                ! The vintage of the order of arithmetic for horizontal regridding.  Dates
                                ! before 20190101 give the same answers as the code did in late 2018, while
                                ! later versions add parentheses for rotational symmetry.  Dates after 20230101
                                ! use reproducing sums for global averages.
LAND_FILL_TEMP = 0.0            !   [degC] default = 0.0
                                ! A value to use to fill in ocean temperatures on land points.
LAND_FILL_SALIN = 35.0          !   [ppt] default = 35.0
                                ! A value to use to fill in ocean salinities on land points.
HORIZ_INTERP_TOL_TEMP = 0.001   !   [degC] default = 0.001
                                ! The tolerance in temperature changes between iterations when interpolating
                                ! from an input dataset using horiz_interp_and_extrap_tracer.  This routine
                                ! converges slowly, so an overly small tolerance can get expensive.
HORIZ_INTERP_TOL_SALIN = 0.001  !   [ppt] default = 0.001
                                ! The tolerance in salinity changes between iterations when interpolating from
                                ! an input dataset using horiz_interp_and_extrap_tracer.  This routine converges
                                ! slowly, so an overly small tolerance can get expensive.
DEPRESS_INITIAL_SURFACE = False !   [Boolean] default = False
                                ! If true,  depress the initial surface to avoid huge tsunamis when a large
                                ! surface pressure is applied.
TRIM_IC_FOR_P_SURF = False      !   [Boolean] default = False
                                ! If true, cuts way the top of the column for initial conditions at the depth
                                ! where the hydrostatic pressure matches the imposed surface pressure which is
                                ! read from file.
REGRID_ACCELERATE_INIT = False  !   [Boolean] default = False
                                ! If true, runs REGRID_ACCELERATE_ITERATIONS iterations of the regridding
                                ! algorithm to push the initial grid to be consistent with the initial
                                ! condition. Useful only for state-based and iterative coordinates.
VELOCITY_CONFIG = "zero"        ! default = "zero"
                                ! A string that determines how the initial velocities are specified for a new
                                ! run:
                                !     file - read velocities from the file specified
                                !       by (VELOCITY_FILE).
                                !     zero - the fluid is initially at rest.
                                !     uniform - the flow is uniform (determined by
                                !       parameters INITIAL_U_CONST and INITIAL_V_CONST).
                                !     rossby_front - a mixed layer front in thermal wind balance.
                                !     soliton - Equatorial Rossby soliton.
                                !     USER - call a user modified routine.
ODA_INCUPD = False              !   [Boolean] default = False
                                ! If true, oda incremental updates will be applied everywhere in the domain.
SPONGE = False                  !   [Boolean] default = False
                                ! If true, sponges may be applied anywhere in the domain. The exact location and
                                ! properties of those sponges are specified via SPONGE_CONFIG.

! === module MOM_diag_mediator ===
NUM_DIAG_COORDS = 1             ! default = 1
                                ! The number of diagnostic vertical coordinates to use. For each coordinate, an
                                ! entry in DIAG_COORDS must be provided.
DIAG_REMAPPING_USE_OM4_SUBCELLS = False !   [Boolean] default = True
                                ! If true, use the OM4 remapping-via-subcells algorithm for diagnostics. See
                                ! REMAPPING_USE_OM4_SUBCELLS for details. We recommend setting this option to
                                ! false.
USE_INDEX_DIAGNOSTIC_AXES = False !   [Boolean] default = False
                                ! If true, use a grid index coordinate convention for diagnostic axes.
DIAG_COORDS = "z Z ZSTAR"       ! default = "z Z ZSTAR"
                                ! A list of string tuples associating diag_table modules to a coordinate
                                ! definition used for diagnostics. Each string is of the form "MODULE_SUFFIX
                                ! PARAMETER_SUFFIX COORDINATE_NAME".
DIAG_MISVAL = 1.0E+20           !   [various] default = 1.0E+20
                                ! Set the default missing value to use for diagnostics.
DIAG_AS_CHKSUM = False          !   [Boolean] default = False
                                ! Instead of writing diagnostics to the diag manager, write a text file
                                ! containing the checksum (bitcount) of the array.
AVAILABLE_DIAGS_FILE = "available_diags.000000" ! default = "available_diags.000000"
                                ! A file into which to write a list of all available ocean diagnostics that can
                                ! be included in a diag_table.
DIAG_COORD_DEF_Z = "FILE:ocean_vgrid.nc,interfaces=zeta" ! default = "WOA09"
                                ! Determines how to specify the coordinate resolution. Valid options are:
                                !  PARAM       - use the vector-parameter DIAG_COORD_RES_Z
                                !  UNIFORM[:N] - uniformly distributed
                                !  FILE:string - read from a file. The string specifies
                                !                the filename and variable name, separated
                                !                by a comma or space, e.g. FILE:lev.nc,dz
                                !                or FILE:lev.nc,interfaces=zw
                                !  WOA09[:N]   - the WOA09 vertical grid (approximately)
                                !  WOA09INT[:N] - layers spanned by the WOA09 depths
                                !  WOA23INT[:N] - layers spanned by the WOA23 depths
                                !  FNC1:string - FNC1:dz_min,H_total,power,precision
                                !  HYBRID:string - read from a file. The string specifies
                                !                the filename and two variable names, separated
                                !                by a comma or space, for sigma-2 and dz. e.g.
                                !                HYBRID:vgrid.nc,sigma2,dz

! === module MOM_MEKE ===
USE_MEKE = True                 !   [Boolean] default = False
                                ! If true, turns on the MEKE scheme which calculates a sub-grid mesoscale eddy
                                ! kinetic energy budget.
MEKE_IN_DYNAMICS = True         !   [Boolean] default = True
                                ! If true, step MEKE forward with the dynamicsotherwise with the tracer
                                ! timestep.
EKE_SOURCE = "prog"             ! default = "prog"
                                ! Determine the where EKE comes from:
                                !   'prog': Calculated solving EKE equation
                                !   'file': Read in from a file
                                !   'dbclient': Retrieved from ML-database
MEKE_DAMPING = 0.0              !   [s-1] default = 0.0
                                ! The local depth-independent MEKE dissipation rate.
MEKE_CD_SCALE = 0.0             !   [nondim] default = 0.0
                                ! The ratio of the bottom eddy velocity to the column mean eddy velocity, i.e.
                                ! sqrt(2*MEKE). This should be less than 1 to account for the surface
                                ! intensification of MEKE.
MEKE_CB = 25.0                  !   [nondim] default = 25.0
                                ! A coefficient in the expression for the ratio of bottom projected eddy energy
                                ! and mean column energy (see Jansen et al. 2015).
MEKE_MIN_GAMMA2 = 1.0E-04       !   [nondim] default = 1.0E-04
                                ! The minimum allowed value of gamma_b^2.
MEKE_CT = 50.0                  !   [nondim] default = 50.0
                                ! A coefficient in the expression for the ratio of barotropic eddy energy and
                                ! mean column energy (see Jansen et al. 2015).
MEKE_GMCOEFF = 1.0              !   [nondim] default = -1.0
                                ! The efficiency of the conversion of potential energy into MEKE by the
                                ! thickness mixing parameterization. If MEKE_GMCOEFF is negative, this
                                ! conversion is not used or calculated.
MEKE_GEOMETRIC = False          !   [Boolean] default = False
                                ! If MEKE_GEOMETRIC is true, uses the GM coefficient formulation from the
                                ! GEOMETRIC framework (Marshall et al., 2012).
MEKE_GEOMETRIC_ALPHA = 0.05     !   [nondim] default = 0.05
                                ! The nondimensional coefficient governing the efficiency of the GEOMETRIC
                                ! thickness diffusion.
MEKE_EQUILIBRIUM_ALT = False    !   [Boolean] default = False
                                ! If true, use an alternative formula for computing the (equilibrium)initial
                                ! value of MEKE.
MEKE_EQUILIBRIUM_RESTORING = False !   [Boolean] default = False
                                ! If true, restore MEKE back to its equilibrium value, which is calculated at
                                ! each time step.
MEKE_FRCOEFF = -1.0             !   [nondim] default = -1.0
                                ! The efficiency of the conversion of mean energy into MEKE.  If MEKE_FRCOEFF is
                                ! negative, this conversion is not used or calculated.
MEKE_BHFRCOEFF = -1.0           !   [nondim] default = -1.0
                                ! The efficiency of the conversion of mean energy into MEKE by the biharmonic
                                ! dissipation.  If MEKE_bhFRCOEFF is negative, this conversion is not used or
                                ! calculated.
MEKE_GMECOEFF = -1.0            !   [nondim] default = -1.0
                                ! The efficiency of the conversion of MEKE into mean energy by GME.  If
                                ! MEKE_GMECOEFF is negative, this conversion is not used or calculated.
MEKE_BGSRC = 1.0E-13            !   [W kg-1] default = 0.0
                                ! A background energy source for MEKE.
MEKE_KH = -1.0                  !   [m2 s-1] default = -1.0
                                ! A background lateral diffusivity of MEKE. Use a negative value to not apply
                                ! lateral diffusion to MEKE.
MEKE_K4 = -1.0                  !   [m4 s-1] default = -1.0
                                ! A lateral bi-harmonic diffusivity of MEKE. Use a negative value to not apply
                                ! bi-harmonic diffusion to MEKE.
MEKE_DTSCALE = 1.0              !   [nondim] default = 1.0
                                ! A scaling factor to accelerate the time evolution of MEKE.
MEKE_KHCOEFF = 1.0              !   [nondim] default = 1.0
                                ! A scaling factor in the expression for eddy diffusivity which is otherwise
                                ! proportional to the MEKE velocity- scale times an eddy mixing-length. This
                                ! factor must be >0 for MEKE to contribute to the thickness/ and tracer
                                ! diffusivity in the rest of the model.
MEKE_USCALE = 0.0               !   [m s-1] default = 0.0
                                ! The background velocity that is combined with MEKE to calculate the bottom
                                ! drag.
MEKE_GM_SRC_ALT = False         !   [Boolean] default = False
                                ! If true, use the GM energy conversion form S^2*N^2*kappa rather than the
                                ! streamfunction for the MEKE GM source term.
MEKE_VISC_DRAG = True           !   [Boolean] default = True
                                ! If true, use the vertvisc_type to calculate the bottom drag acting on MEKE.
MEKE_KHTH_FAC = 0.0             !   [nondim] default = 0.0
                                ! A factor that maps MEKE%Kh to KhTh.
MEKE_KHTR_FAC = 0.0             !   [nondim] default = 0.0
                                ! A factor that maps MEKE%Kh to KhTr.
MEKE_KHMEKE_FAC = 1.0           !   [nondim] default = 0.0
                                ! A factor that maps MEKE%Kh to Kh for MEKE itself.
MEKE_OLD_LSCALE = False         !   [Boolean] default = False
                                ! If true, use the old formula for length scale which is a function of grid
                                ! spacing and deformation radius.
MEKE_MIN_LSCALE = False         !   [Boolean] default = False
                                ! If true, use a strict minimum of provided length scales rather than harmonic
                                ! mean.
MEKE_RD_MAX_SCALE = False       !   [Boolean] default = False
                                ! If true, the length scale used by MEKE is the minimum of the deformation
                                ! radius or grid-spacing. Only used if MEKE_OLD_LSCALE=True
MEKE_VISCOSITY_COEFF_KU = 0.0   !   [nondim] default = 0.0
                                ! If non-zero, is the scaling coefficient in the expression forviscosity used to
                                ! parameterize harmonic lateral momentum mixing byunresolved eddies represented
                                ! by MEKE. Can be negative torepresent backscatter from the unresolved eddies.
MEKE_VISCOSITY_COEFF_AU = 0.0   !   [nondim] default = 0.0
                                ! If non-zero, is the scaling coefficient in the expression forviscosity used to
                                ! parameterize biharmonic lateral momentum mixing byunresolved eddies
                                ! represented by MEKE. Can be negative torepresent backscatter from the
                                ! unresolved eddies.
MEKE_FIXED_MIXING_LENGTH = 0.0  !   [m] default = 0.0
                                ! If positive, is a fixed length contribution to the expression for mixing
                                ! length used in MEKE-derived diffusivity.
MEKE_FIXED_TOTAL_DEPTH = True   !   [Boolean] default = True
                                ! If true, use the nominal bathymetric depth as the estimate of the time-varying
                                ! ocean depth.  Otherwise base the depth on the total ocean massper unit area.
MEKE_ALPHA_DEFORM = 0.0         !   [nondim] default = 0.0
                                ! If positive, is a coefficient weighting the deformation scale in the
                                ! expression for mixing length used in MEKE-derived diffusivity.
MEKE_ALPHA_RHINES = 0.15        !   [nondim] default = 0.0
                                ! If positive, is a coefficient weighting the Rhines scale in the expression for
                                ! mixing length used in MEKE-derived diffusivity.
MEKE_ALPHA_EADY = 0.15          !   [nondim] default = 0.0
                                ! If positive, is a coefficient weighting the Eady length scale in the
                                ! expression for mixing length used in MEKE-derived diffusivity.
MEKE_ALPHA_FRICT = 0.0          !   [nondim] default = 0.0
                                ! If positive, is a coefficient weighting the frictional arrest scale in the
                                ! expression for mixing length used in MEKE-derived diffusivity.
MEKE_ALPHA_GRID = 0.0           !   [nondim] default = 0.0
                                ! If positive, is a coefficient weighting the grid-spacing as a scale in the
                                ! expression for mixing length used in MEKE-derived diffusivity.
MEKE_COLD_START = False         !   [Boolean] default = False
                                ! If true, initialize EKE to zero. Otherwise a local equilibrium solution is
                                ! used as an initial condition for EKE.
MEKE_BACKSCAT_RO_C = 0.0        !   [nondim] default = 0.0
                                ! The coefficient in the Rossby number function for scaling the biharmonic
                                ! frictional energy source. Setting to non-zero enables the Rossby number
                                ! function.
MEKE_BACKSCAT_RO_POW = 0.0      !   [nondim] default = 0.0
                                ! The power in the Rossby number function for scaling the biharmonic frictional
                                ! energy source.
MEKE_ADVECTION_FACTOR = 0.0     !   [nondim] default = 0.0
                                ! A scale factor in front of advection of eddy energy. Zero turns advection off.
                                ! Using unity would be normal but other values could accommodate a mismatch
                                ! between the advecting barotropic flow and the vertical structure of MEKE.
MEKE_TOPOGRAPHIC_BETA = 0.0     !   [nondim] default = 0.0
                                ! A scale factor to determine how much topographic beta is weighed in computing
                                ! beta in the expression of Rhines scale. Use 1 if full topographic beta effect
                                ! is considered; use 0 if it's completely ignored.
SQG_USE_MEKE = False            !   [Boolean] default = False
                                ! If true, the eddy scale of MEKE is used for the SQG vertical structure
CDRAG = 0.003                   !   [nondim] default = 0.003
                                ! CDRAG is the drag coefficient relating the magnitude of the velocity field to
                                ! the bottom stress.
MEKE_CDRAG = 0.003              !   [nondim] default = 0.003
                                ! Drag coefficient relating the magnitude of the velocity field to the bottom
                                ! stress in MEKE.

! === module MOM_lateral_mixing_coeffs ===
USE_VARIABLE_MIXING = True      !   [Boolean] default = False
                                ! If true, the variable mixing code will be called.  This allows diagnostics to
                                ! be created even if the scheme is not used.  If KHTR_SLOPE_CFF>0 or
                                ! KhTh_Slope_Cff>0, this is set to true regardless of what is in the parameter
                                ! file.
USE_VISBECK = False             !   [Boolean] default = False
                                ! If true, use the Visbeck et al. (1997) formulation for
                                ! thickness diffusivity.
RESOLN_SCALED_KH = True         !   [Boolean] default = False
                                ! If true, the Laplacian lateral viscosity is scaled away when the first
                                ! baroclinic deformation radius is well resolved.
DEPTH_SCALED_KHTH = False       !   [Boolean] default = False
                                ! If true, KHTH is scaled away when the depth is shallowerthan a reference
                                ! depth: KHTH = MIN(1,H/H0)**N * KHTH, where H0 is a reference depth, controlled
                                ! via DEPTH_SCALED_KHTH_H0, and the exponent (N) is controlled via
                                ! DEPTH_SCALED_KHTH_EXP.
RESOLN_SCALED_KHTH = True       !   [Boolean] default = False
                                ! If true, the interface depth diffusivity is scaled away when the first
                                ! baroclinic deformation radius is well resolved.
RESOLN_SCALED_KHTR = False      !   [Boolean] default = False
                                ! If true, the epipycnal tracer diffusivity is scaled away when the first
                                ! baroclinic deformation radius is well resolved.
RESOLN_USE_EBT = False          !   [Boolean] default = False
                                ! If true, uses the equivalent barotropic wave speed instead of first baroclinic
                                ! wave for calculating the resolution fn.
BACKSCAT_EBT_POWER = 0.0        !   [nondim] default = 0.0
                                ! Power to raise EBT vertical structure to when backscatter has vertical
                                ! structure.
BS_USE_SQG_STRUCT = False       !   [Boolean] default = False
                                ! If true, the SQG vertical structure is used for backscatter on the condition
                                ! that BS_EBT_power=0
SQG_EXPO = 1.0                  !   [nondim] default = 1.0
                                ! Nondimensional exponent coeffecient of the SQG mode that is used for the
                                ! vertical struture of diffusivities.
KHTH_USE_EBT_STRUCT = False     !   [Boolean] default = False
                                ! If true, uses the equivalent barotropic structure as the vertical structure of
                                ! thickness diffusivity.
KHTH_USE_SQG_STRUCT = False     !   [Boolean] default = False
                                ! If true, uses the surface quasigeostrophic structure as the vertical structure
                                ! of thickness diffusivity.
KHTR_USE_EBT_STRUCT = False     !   [Boolean] default = False
                                ! If true, uses the equivalent barotropic structure as the vertical structure of
                                ! tracer diffusivity.
KHTR_USE_SQG_STRUCT = False     !   [Boolean] default = False
                                ! If true, uses the surface quasigeostrophic structure as the vertical structure
                                ! of tracer diffusivity.
KD_GL90_USE_EBT_STRUCT = False  !   [Boolean] default = False
                                ! If true, uses the equivalent barotropic structure as the vertical structure of
                                ! diffusivity in the GL90 scheme.
KD_GL90_USE_SQG_STRUCT = False  !   [Boolean] default = False
                                ! If true, uses the equivalent barotropic structure as the vertical structure of
                                ! diffusivity in the GL90 scheme.
KHTH_SLOPE_CFF = 0.0            !   [nondim] default = 0.0
                                ! The nondimensional coefficient in the Visbeck formula for the interface depth
                                ! diffusivity
KHTR_SLOPE_CFF = 0.25           !   [nondim] default = 0.0
                                ! The nondimensional coefficient in the Visbeck formula for the epipycnal tracer
                                ! diffusivity
USE_STORED_SLOPES = True        !   [Boolean] default = False
                                ! If true, the isopycnal slopes are calculated once and stored for re-use. This
                                ! uses more memory but avoids calling the equation of state more times than
                                ! should be necessary.
VERY_SMALL_FREQUENCY = 1.0E-17  !   [s-1] default = 1.0E-17
                                ! A miniscule frequency that is used to avoid division by 0.  The default value
                                ! is roughly (pi / (the age of the universe)).
USE_STANLEY_ISO = False         !   [Boolean] default = False
                                ! If true, turn on Stanley SGS T variance parameterization in isopycnal slope
                                ! code.
VISBECK_MAX_SLOPE = 0.0         !   [nondim] default = 0.0
                                ! If non-zero, is an upper bound on slopes used in the Visbeck formula for
                                ! diffusivity. This does not affect the isopycnal slope calculation used within
                                ! thickness diffusion.
KD_SMOOTH = 1.0E-06             !   [m2 s-1] default = 1.0E-06
                                ! A diapycnal diffusivity that is used to interpolate more sensible values of T
                                ! & S into thin layers.
USE_SIMPLER_EADY_GROWTH_RATE = False !   [Boolean] default = False
                                ! If true, use a simpler method to calculate the Eady growth rate that avoids
                                ! division by layer thickness. Recommended.
VARMIX_KTOP = 2                 !   [nondim] default = 2
                                ! The layer number at which to start vertical integration of S*N for purposes of
                                ! finding the Eady growth rate.
VISBECK_L_SCALE = 0.0           !   [m or nondim] default = 0.0
                                ! The fixed length scale in the Visbeck formula, or if negative a nondimensional
                                ! scaling factor relating this length scale squared to the cell areas.
KH_RES_SCALE_COEF = 1.0         !   [nondim] default = 1.0
                                ! A coefficient that determines how KhTh is scaled away if RESOLN_SCALED_... is
                                ! true, as F = 1 / (1 + (KH_RES_SCALE_COEF*Rd/dx)^KH_RES_FN_POWER).
KH_RES_FN_POWER = 2             ! default = 2
                                ! The power of dx/Ld in the Kh resolution function.  Any positive integer may be
                                ! used, although even integers are more efficient to calculate.  Setting this
                                ! greater than 100 results in a step-function being used.
VISC_RES_SCALE_COEF = 1.0       !   [nondim] default = 1.0
                                ! A coefficient that determines how Kh is scaled away if RESOLN_SCALED_... is
                                ! true, as F = 1 / (1 + (KH_RES_SCALE_COEF*Rd/dx)^KH_RES_FN_POWER). This
                                ! function affects lateral viscosity, Kh, and not KhTh.
VISC_RES_FN_POWER = 2           ! default = 2
                                ! The power of dx/Ld in the Kh resolution function.  Any positive integer may be
                                ! used, although even integers are more efficient to calculate.  Setting this
                                ! greater than 100 results in a step-function being used. This function affects
                                ! lateral viscosity, Kh, and not KhTh.
INTERPOLATE_RES_FN = False      !   [Boolean] default = False
                                ! If true, interpolate the resolution function to the velocity points from the
                                ! thickness points; otherwise interpolate the wave speed and calculate the
                                ! resolution function independently at each point.
GILL_EQUATORIAL_LD = True       !   [Boolean] default = True
                                ! If true, uses Gill's definition of the baroclinic equatorial deformation
                                ! radius, otherwise, if false, use Pedlosky's definition. These definitions
                                ! differ by a factor of 2 in front of the beta term in the denominator. Gill's
                                ! is the more appropriate definition.
INTERNAL_WAVE_SPEED_TOL = 0.001 !   [nondim] default = 0.001
                                ! The fractional tolerance for finding the wave speeds.
INTERNAL_WAVE_SPEED_MIN = 0.0   !   [m s-1] default = 0.0
                                ! A floor in the first mode speed below which 0 used instead.
INTERNAL_WAVE_SPEED_BETTER_EST = True !   [Boolean] default = True
                                ! If true, use a more robust estimate of the first mode wave speed as the
                                ! starting point for iterations.
EBT_REMAPPING_USE_OM4_SUBCELLS = False !   [Boolean] default = True
                                ! If true, use the OM4 remapping-via-subcells algorithm for calculating EBT
                                ! structure. See REMAPPING_USE_OM4_SUBCELLS for details. We recommend setting
                                ! this option to false.
USE_QG_LEITH_GM = False         !   [Boolean] default = False
                                ! If true, use the QG Leith viscosity as the GM coefficient.

! === module MOM_set_visc ===
SET_VISC_ANSWER_DATE = 99991231 ! default = 99991231
                                ! The vintage of the order of arithmetic and expressions in the set viscosity
                                ! calculations.  Values below 20190101 recover the answers from the end of 2018,
                                ! while higher values use updated and more robust forms of the same expressions.
BOTTOMDRAGLAW = True            !   [Boolean] default = True
                                ! If true, the bottom stress is calculated with a drag law of the form
                                ! c_drag*|u|*u. The velocity magnitude may be an assumed value or it may be
                                ! based on the actual velocity in the bottommost HBBL, depending on LINEAR_DRAG.
DRAG_AS_BODY_FORCE = False      !   [Boolean] default = False
                                ! If true, the bottom stress is imposed as an explicit body force applied over a
                                ! fixed distance from the bottom, rather than as an implicit calculation based
                                ! on an enhanced near-bottom viscosity. The thickness of the bottom boundary
                                ! layer is HBBL.
CHANNEL_DRAG = True             !   [Boolean] default = False
                                ! If true, the bottom drag is exerted directly on each layer proportional to the
                                ! fraction of the bottom it overlies.
LINEAR_DRAG = False             !   [Boolean] default = False
                                ! If LINEAR_DRAG and BOTTOMDRAGLAW are defined the drag law is
                                ! cdrag*DRAG_BG_VEL*u.
PRANDTL_TURB = 1.0              !   [nondim] default = 1.0
                                ! The turbulent Prandtl number applied to shear instability.
DYNAMIC_VISCOUS_ML = False      !   [Boolean] default = False
                                ! If true, use a bulk Richardson number criterion to determine the mixed layer
                                ! thickness for viscosity.
HBBL = 10.0                     !   [m]
                                ! The thickness of a bottom boundary layer with a viscosity increased by
                                ! KV_EXTRA_BBL if BOTTOMDRAGLAW is not defined, or the thickness over which
                                ! near-bottom velocities are averaged for the drag law if BOTTOMDRAGLAW is
                                ! defined but LINEAR_DRAG is not.
BBL_USE_TIDAL_BG = False        !   [Boolean] default = False
                                ! Flag to use the tidal RMS amplitude in place of constant background velocity
                                ! for computing u* in the BBL. This flag is only used when BOTTOMDRAGLAW is true
                                ! and LINEAR_DRAG is false.
DRAG_BG_VEL = 0.1               !   [m s-1] default = 0.0
                                ! DRAG_BG_VEL is either the assumed bottom velocity (with LINEAR_DRAG) or an
                                ! unresolved  velocity that is combined with the resolved velocity to estimate
                                ! the velocity magnitude.  DRAG_BG_VEL is only used when BOTTOMDRAGLAW is
                                ! defined.
BBL_USE_EOS = True              !   [Boolean] default = True
                                ! If true, use the equation of state in determining the properties of the bottom
                                ! boundary layer.  Otherwise use the layer target potential densities.  The
                                ! default of this parameter is the value of USE_EOS.
BBL_THICK_MIN = 0.1             !   [m] default = 0.0
                                ! The minimum bottom boundary layer thickness that can be used with
                                ! BOTTOMDRAGLAW. This might be Kv/(cdrag*drag_bg_vel) to give Kv as the minimum
                                ! near-bottom viscosity.
HTBL_SHELF_MIN = 0.1            !   [m] default = 0.1
                                ! The minimum top boundary layer thickness that can be used with BOTTOMDRAGLAW.
                                ! This might be Kv/(cdrag*drag_bg_vel) to give Kv as the minimum near-top
                                ! viscosity.
HTBL_SHELF = 10.0               !   [m] default = 10.0
                                ! The thickness over which near-surface velocities are averaged for the drag law
                                ! under an ice shelf.  By default this is the same as HBBL
KV = 0.0                        !   [m2 s-1]
                                ! The background kinematic viscosity in the interior. The molecular value, ~1e-6
                                ! m2 s-1, may be used.
KV_BBL_MIN = 0.0                !   [m2 s-1] default = 0.0
                                ! The minimum viscosities in the bottom boundary layer.
KV_TBL_MIN = 0.0                !   [m2 s-1] default = 0.0
                                ! The minimum viscosities in the top boundary layer.
CORRECT_BBL_BOUNDS = False      !   [Boolean] default = False
                                ! If true, uses the correct bounds on the BBL thickness and viscosity so that
                                ! the bottom layer feels the intended drag.
SMAG_CONST_CHANNEL = 0.15       !   [nondim] default = 0.15
                                ! The nondimensional Laplacian Smagorinsky constant used in calculating the
                                ! channel drag if it is enabled.  The default is to use the same value as
                                ! SMAG_LAP_CONST if it is defined, or 0.15 if it is not. The value used is also
                                ! 0.15 if the specified value is negative.
TRIG_CHANNEL_DRAG_WIDTHS = True !   [Boolean] default = True
                                ! If true, use trigonometric expressions to determine the fractional open
                                ! interface lengths for concave topography.
CHANNEL_DRAG_MAX_BBL_THICK = 5.0 !   [m] default = 5.0
                                ! The maximum bottom boundary layer thickness over which the channel drag is
                                ! exerted, or a negative value for no fixed limit, instead basing the BBL
                                ! thickness on the bottom stress, rotation and stratification.  The default is
                                ! proportional to HBBL if USE_JACKSON_PARAM or DRAG_AS_BODY_FORCE is true.

! === module MOM_thickness_diffuse ===
KHTH = 0.0                      !   [m2 s-1] default = 0.0
                                ! The background horizontal thickness diffusivity.
READ_KHTH = False               !   [Boolean] default = False
                                ! If true, read a file (given by KHTH_FILE) containing the spatially varying
                                ! horizontal isopycnal height diffusivity.
KHTH_MIN = 0.0                  !   [m2 s-1] default = 0.0
                                ! The minimum horizontal thickness diffusivity.
KHTH_MAX = 0.0                  !   [m2 s-1] default = 0.0
                                ! The maximum horizontal thickness diffusivity.
KHTH_MAX_CFL = 0.1              !   [nondimensional] default = 0.8
                                ! The maximum value of the local diffusive CFL ratio that is permitted for the
                                ! thickness diffusivity. 1.0 is the marginally unstable value in a pure layered
                                ! model, but much smaller numbers (e.g. 0.1) seem to work better for ALE-based
                                ! models.
KH_ETA_CONST = 0.0              !   [m2 s-1] default = 0.0
                                ! The background horizontal diffusivity of the interface heights (without
                                ! considering the layer density structure).  If diffusive CFL limits are
                                ! encountered, the diffusivities of the isopycnals and the interfaces heights
                                ! are scaled back proportionately.
KH_ETA_VEL_SCALE = 0.0          !   [m s-1] default = 0.0
                                ! A velocity scale that is multiplied by the grid spacing to give a contribution
                                ! to the horizontal diffusivity of the interface heights (without considering
                                ! the layer density structure).
DETANGLE_INTERFACES = False     !   [Boolean] default = False
                                ! If defined add 3-d structured enhanced interface height diffusivities to
                                ! horizontally smooth jagged layers.
KHTH_SLOPE_MAX = 0.01           !   [nondim] default = 0.01
                                ! A slope beyond which the calculated isopycnal slope is not reliable and is
                                ! scaled away.
KHTH_USE_FGNV_STREAMFUNCTION = False !   [Boolean] default = False
                                ! If true, use the streamfunction formulation of Ferrari et al., 2010, which
                                ! effectively emphasizes graver vertical modes by smoothing in the vertical.
USE_STANLEY_GM = False          !   [Boolean] default = False
                                ! If true, turn on Stanley SGS T variance parameterization in GM code.
USE_KH_IN_MEKE = False          !   [Boolean] default = False
                                ! If true, uses the thickness diffusivity calculated here to diffuse MEKE.
USE_GME = False                 !   [Boolean] default = False
                                ! If true, use the GM+E backscatter scheme in association with the Gent and
                                ! McWilliams parameterization.
USE_GM_WORK_BUG = False         !   [Boolean] default = False
                                ! If true, compute the top-layer work tendency on the u-grid with the incorrect
                                ! sign, for legacy reproducibility.
STOCH_EOS = False               !   [Boolean] default = False
                                ! If true, stochastic perturbations are applied to the EOS in the PGF.
STANLEY_COEFF = -1.0            !   [nondim] default = -1.0
                                ! Coefficient correlating the temperature gradient and SGS T variance.

! === module MOM_dynamics_split_RK2 ===
TIDES = False                   !   [Boolean] default = False
                                ! If true, apply tidal momentum forcing.
CALCULATE_SAL = False           !   [Boolean] default = False
                                ! If true, calculate self-attraction and loading.
BE = 0.6                        !   [nondim] default = 0.6
                                ! If SPLIT is true, BE determines the relative weighting of a  2nd-order
                                ! Runga-Kutta baroclinic time stepping scheme (0.5) and a backward Euler scheme
                                ! (1) that is used for the Coriolis and inertial terms.  BE may be from 0.5 to
                                ! 1, but instability may occur near 0.5. BE is also applicable if SPLIT is false
                                ! and USE_RK2 is true.
BEGW = 0.0                      !   [nondim] default = 0.0
                                ! If SPLIT is true, BEGW is a number from 0 to 1 that controls the extent to
                                ! which the treatment of gravity waves is forward-backward (0) or simulated
                                ! backward Euler (1).  0 is almost always used. If SPLIT is false and USE_RK2 is
                                ! true, BEGW can be between 0 and 0.5 to damp gravity waves.
SPLIT_BOTTOM_STRESS = False     !   [Boolean] default = False
                                ! If true, provide the bottom stress calculated by the vertical viscosity to the
                                ! barotropic solver.
BT_USE_LAYER_FLUXES = True      !   [Boolean] default = True
                                ! If true, use the summed layered fluxes plus an adjustment due to the change in
                                ! the barotropic velocity in the barotropic continuity equation.
STORE_CORIOLIS_ACCEL = True     !   [Boolean] default = True
                                ! If true, calculate the Coriolis accelerations at the end of each timestep for
                                ! use in the predictor step of the next split RK2 timestep.
FPMIX = False                   !   [Boolean] default = False
                                ! If true, apply profiles of momentum flux magnitude and  direction
VISC_REM_BUG = False            !   [Boolean] default = True
                                ! If true, visc_rem_[uv] in split mode is incorrectly calculated or accounted
                                ! for in two places. This parameter controls the defaults of two individual
                                ! flags, VISC_REM_TIMESTEP_BUG in MOM_dynamics_split_RK2(b) and
                                ! VISC_REM_BT_WEIGHT_BUG in MOM_barotropic.
VISC_REM_TIMESTEP_BUG = False   !   [Boolean] default = False
                                ! If true, recover a bug that uses dt_pred rather than dt in vertvisc_remnant()
                                ! at the end of predictor stage for the following continuity() and btstep()
                                ! calls in the corrector step. Default of this flag is set by VISC_REM_BUG

! === module MOM_continuity_PPM ===
MONOTONIC_CONTINUITY = False    !   [Boolean] default = False
                                ! If true, CONTINUITY_PPM uses the Colella and Woodward monotonic limiter.  The
                                ! default (false) is to use a simple positive definite limiter.
SIMPLE_2ND_PPM_CONTINUITY = False !   [Boolean] default = False
                                ! If true, CONTINUITY_PPM uses a simple 2nd order (arithmetic mean)
                                ! interpolation of the edge values. This may give better PV conservation
                                ! properties. While it formally reduces the accuracy of the continuity solver
                                ! itself in the strongly advective limit, it does not reduce the overall order
                                ! of accuracy of the dynamic core.
UPWIND_1ST_CONTINUITY = False   !   [Boolean] default = False
                                ! If true, CONTINUITY_PPM becomes a 1st-order upwind continuity solver.  This
                                ! scheme is highly diffusive but may be useful for debugging or in single-column
                                ! mode where its minimal stencil is useful.
ETA_TOLERANCE = 1.0E-06         !   [m] default = 3.75E-09
                                ! The tolerance for the differences between the barotropic and baroclinic
                                ! estimates of the sea surface height due to the fluxes through each face.  The
                                ! total tolerance for SSH is 4 times this value.  The default is
                                ! 0.5*NK*ANGSTROM, and this should not be set less than about
                                ! 10^-15*MAXIMUM_DEPTH.
VELOCITY_TOLERANCE = 3.0E+08    !   [m s-1] default = 3.0E+08
                                ! The tolerance for barotropic velocity discrepancies between the barotropic
                                ! solution and  the sum of the layer thicknesses.
CONT_PPM_AGGRESS_ADJUST = False !   [Boolean] default = False
                                ! If true, allow the adjusted velocities to have a relative CFL change up to
                                ! 0.5.
CONT_PPM_VOLUME_BASED_CFL = False !   [Boolean] default = False
                                ! If true, use the ratio of the open face lengths to the tracer cell areas when
                                ! estimating CFL numbers.  The default is set by CONT_PPM_AGGRESS_ADJUST.
CONTINUITY_CFL_LIMIT = 0.5      !   [nondim] default = 0.5
                                ! The maximum CFL of the adjusted velocities.
CONT_PPM_BETTER_ITER = True     !   [Boolean] default = True
                                ! If true, stop corrective iterations using a velocity based criterion and only
                                ! stop if the iteration is better than all predecessors.
CONT_PPM_USE_VISC_REM_MAX = True !   [Boolean] default = True
                                ! If true, use more appropriate limiting bounds for corrections in strongly
                                ! viscous columns.
CONT_PPM_MARGINAL_FACE_AREAS = True !   [Boolean] default = True
                                ! If true, use the marginal face areas from the continuity solver for use as the
                                ! weights in the barotropic solver. Otherwise use the transport averaged areas.

! === module MOM_CoriolisAdv ===
NOSLIP = False                  !   [Boolean] default = False
                                ! If true, no slip boundary conditions are used; otherwise free slip boundary
                                ! conditions are assumed. The implementation of the free slip BCs on a C-grid is
                                ! much cleaner than the no slip BCs. The use of free slip BCs is strongly
                                ! encouraged, and no slip BCs are not used with the biharmonic viscosity.
CORIOLIS_EN_DIS = False         !   [Boolean] default = False
                                ! If true, two estimates of the thickness fluxes are used to estimate the
                                ! Coriolis term, and the one that dissipates energy relative to the other one is
                                ! used.
CORIOLIS_SCHEME = "SADOURNY75_ENERGY" ! default = "SADOURNY75_ENERGY"
                                ! CORIOLIS_SCHEME selects the discretization for the Coriolis terms. Valid
                                ! values are:
                                !    SADOURNY75_ENERGY - Sadourny, 1975; energy cons.
                                !    ARAKAWA_HSU90     - Arakawa & Hsu, 1990
                                !    SADOURNY75_ENSTRO - Sadourny, 1975; enstrophy cons.
                                !    ARAKAWA_LAMB81    - Arakawa & Lamb, 1981; En. + Enst.
                                !    ARAKAWA_LAMB_BLEND - A blend of Arakawa & Lamb with
                                !                         Arakawa & Hsu and Sadourny energy
BOUND_CORIOLIS = True           !   [Boolean] default = False
                                ! If true, the Coriolis terms at u-points are bounded by the four estimates of
                                ! (f+rv)v from the four neighboring v-points, and similarly at v-points.  This
                                ! option would have no effect on the SADOURNY Coriolis scheme if it were
                                ! possible to use centered difference thickness fluxes.
KE_SCHEME = "KE_ARAKAWA"        ! default = "KE_ARAKAWA"
                                ! KE_SCHEME selects the discretization for acceleration due to the kinetic
                                ! energy gradient. Valid values are:
                                !    KE_ARAKAWA, KE_SIMPLE_GUDONOV, KE_GUDONOV
PV_ADV_SCHEME = "PV_ADV_CENTERED" ! default = "PV_ADV_CENTERED"
                                ! PV_ADV_SCHEME selects the discretization for PV advection. Valid values are:
                                !    PV_ADV_CENTERED - centered (aka Sadourny, 75)
                                !    PV_ADV_UPWIND1  - upwind, first order

! === module MOM_PressureForce ===
ANALYTIC_FV_PGF = True          !   [Boolean] default = True
                                ! If true the pressure gradient forces are calculated with a finite volume form
                                ! that analytically integrates the equations of state in pressure to avoid any
                                ! possibility of numerical thermobaric instability, as described in Adcroft et
                                ! al., O. Mod. (2008).

! === module MOM_PressureForce_FV ===
RHO_PGF_REF = 1035.0            !   [kg m-3] default = 1035.0
                                ! The reference density that is subtracted off when calculating pressure
                                ! gradient forces.  Its inverse is subtracted off of specific volumes when in
                                ! non-Boussinesq mode.  The default is RHO_0.
SSH_IN_EOS_PRESSURE_FOR_PGF = False !   [Boolean] default = False
                                ! If true, include contributions from the sea surface height in the height-based
                                ! pressure used in the equation of state calculations for the Boussinesq
                                ! pressure gradient forces, including adjustments for atmospheric or sea-ice
                                ! pressure.
MASS_WEIGHT_IN_PRESSURE_GRADIENT = True !   [Boolean] default = False
                                ! If true, use mass weighting when interpolating T/S for integrals near the
                                ! bathymetry in FV pressure gradient calculations.
MASS_WEIGHT_IN_PRESSURE_GRADIENT_TOP = False !   [Boolean] default = False
                                ! If true and MASS_WEIGHT_IN_PRESSURE_GRADIENT is true, use mass weighting when
                                ! interpolating T/S for integrals near the top of the water column in FV
                                ! pressure gradient calculations.
CORRECTION_INTXPA = False       !   [Boolean] default = False
                                ! If true, use a correction for surface pressure curvature in intx_pa.
RESET_INTXPA_INTEGRAL = False   !   [Boolean] default = False
                                ! If true, reset INTXPA to match pressures at first nonvanished cell. Includes
                                ! pressure correction.
USE_INACCURATE_PGF_RHO_ANOM = False !   [Boolean] default = False
                                ! If true, use a form of the PGF that uses the reference density in an
                                ! inaccurate way. This is not recommended.
RECONSTRUCT_FOR_PRESSURE = True !   [Boolean] default = True
                                ! If True, use vertical reconstruction of T & S within the integrals of the FV
                                ! pressure gradient calculation. If False, use the constant-by-layer algorithm.
                                ! The default is set by USE_REGRIDDING.
PRESSURE_RECONSTRUCTION_SCHEME = 1 ! default = 1
                                ! Order of vertical reconstruction of T/S to use in the integrals within the FV
                                ! pressure gradient calculation.
                                !  0: PCM or no reconstruction.
                                !  1: PLM reconstruction.
                                !  2: PPM reconstruction.
BOUNDARY_EXTRAPOLATION_PRESSURE = True !   [Boolean] default = True
                                ! If true, the reconstruction of T & S for pressure in boundary cells is
                                ! extrapolated, rather than using PCM in these cells. If true, the same order
                                ! polynomial is used as is used for the interior cells.
USE_STANLEY_PGF = False         !   [Boolean] default = False
                                ! If true, turn on Stanley SGS T variance parameterization in PGF code.

! === module MOM_Zanna_Bolton ===
USE_ZB2020 = False              !   [Boolean] default = False
                                ! If true, turns on Zanna-Bolton-2020 (ZB) subgrid momentum parameterization of
                                ! mesoscale eddies.

! === module MOM_hor_visc ===
USE_CONT_THICKNESS = False      !   [Boolean] default = False
                                ! If true, use thickness at velocity points from continuity solver. This option
                                ! currently only works with split mode.
LAPLACIAN = True                !   [Boolean] default = False
                                ! If true, use a Laplacian horizontal viscosity.
KH = 0.0                        !   [m2 s-1] default = 0.0
                                ! The background Laplacian horizontal viscosity.
KH_BG_MIN = 0.0                 !   [m2 s-1] default = 0.0
                                ! The minimum value allowed for Laplacian horizontal viscosity, KH.
KH_VEL_SCALE = 0.0              !   [m s-1] default = 0.0
                                ! The velocity scale which is multiplied by the grid spacing to calculate the
                                ! Laplacian viscosity. The final viscosity is the largest of this scaled
                                ! viscosity, the Smagorinsky and Leith viscosities, and KH.
KH_SIN_LAT = 0.0                !   [m2 s-1] default = 0.0
                                ! The amplitude of a latitudinally-dependent background viscosity of the form
                                ! KH_SIN_LAT*(SIN(LAT)**KH_PWR_OF_SINE).
SMAGORINSKY_KH = False          !   [Boolean] default = False
                                ! If true, use a Smagorinsky nonlinear eddy viscosity.
LEITH_KH = False                !   [Boolean] default = False
                                ! If true, use a Leith nonlinear eddy viscosity.
RES_SCALE_MEKE_VISC = False     !   [Boolean] default = False
                                ! If true, the viscosity contribution from MEKE is scaled by the resolution
                                ! function.
BOUND_KH = True                 !   [Boolean] default = True
                                ! If true, the Laplacian coefficient is locally limited to be stable.
BETTER_BOUND_KH = True          !   [Boolean] default = True
                                ! If true, the Laplacian coefficient is locally limited to be stable with a
                                ! better bounding than just BOUND_KH.
EY24_EBT_BS = False             !   [Boolean] default = False
                                ! If true, use the the backscatter scheme (EBT mode with kill switch)developed
                                ! by Yankovsky et al. (2024).
ANISOTROPIC_VISCOSITY = False   !   [Boolean] default = False
                                ! If true, allow anistropic viscosity in the Laplacian horizontal viscosity.
ADD_LES_VISCOSITY = False       !   [Boolean] default = False
                                ! If true, adds the viscosity from Smagorinsky and Leith to the background
                                ! viscosity instead of taking the maximum.
BIHARMONIC = True               !   [Boolean] default = True
                                ! If true, use a biharmonic horizontal viscosity. BIHARMONIC may be used with
                                ! LAPLACIAN.
AH = 0.0                        !   [m4 s-1] default = 0.0
                                ! The background biharmonic horizontal viscosity.
AH_VEL_SCALE = 0.01             !   [m s-1] default = 0.0
                                ! The velocity scale which is multiplied by the cube of the grid spacing to
                                ! calculate the biharmonic viscosity. The final viscosity is the largest of this
                                ! scaled viscosity, the Smagorinsky and Leith viscosities, and AH.
AH_TIME_SCALE = 0.0             !   [s] default = 0.0
                                ! A time scale whose inverse is multiplied by the fourth power of the grid
                                ! spacing to calculate biharmonic viscosity. The final viscosity is the largest
                                ! of all viscosity formulations in use. 0.0 means that it's not used.
SMAGORINSKY_AH = True           !   [Boolean] default = False
                                ! If true, use a biharmonic Smagorinsky nonlinear eddy viscosity.
LEITH_AH = False                !   [Boolean] default = False
                                ! If true, use a biharmonic Leith nonlinear eddy viscosity.
USE_LEITHY = False              !   [Boolean] default = False
                                ! If true, use a biharmonic Leith nonlinear eddy viscosity together with a
                                ! harmonic backscatter.
BOUND_AH = True                 !   [Boolean] default = True
                                ! If true, the biharmonic coefficient is locally limited to be stable.
BETTER_BOUND_AH = True          !   [Boolean] default = True
                                ! If true, the biharmonic coefficient is locally limited to be stable with a
                                ! better bounding than just BOUND_AH.
RE_AH = 0.0                     !   [nondim] default = 0.0
                                ! If nonzero, the biharmonic coefficient is scaled so that the biharmonic
                                ! Reynolds number is equal to this.
BACKSCATTER_UNDERBOUND = False  !   [Boolean] default = True
                                ! If true, the bounds on the biharmonic viscosity are allowed to increase where
                                ! the Laplacian viscosity is negative (due to backscatter parameterizations)
                                ! beyond the largest timestep-dependent stable values of biharmonic viscosity
                                ! when no Laplacian viscosity is applied.  The default is true for historical
                                ! reasons, but this option probably should not be used because it can contribute
                                ! to numerical instabilities.
SMAG_BI_CONST = 0.06            !   [nondim] default = 0.0
                                ! The nondimensional biharmonic Smagorinsky constant, typically 0.015 - 0.06.
BOUND_CORIOLIS_BIHARM = True    !   [Boolean] default = True
                                ! If true use a viscosity that increases with the square of the velocity shears,
                                ! so that the resulting viscous drag is of comparable magnitude to the Coriolis
                                ! terms when the velocity differences between adjacent grid points is
                                ! 0.5*BOUND_CORIOLIS_VEL.  The default is the value of BOUND_CORIOLIS (or
                                ! false).
BOUND_CORIOLIS_VEL = 6.0        !   [m s-1] default = 6.0
                                ! The velocity scale at which BOUND_CORIOLIS_BIHARM causes the biharmonic drag
                                ! to have comparable magnitude to the Coriolis acceleration.  The default is set
                                ! by MAXVEL.
USE_LAND_MASK_FOR_HVISC = True  !   [Boolean] default = True
                                ! If true, use the land mask for the computation of thicknesses at velocity
                                ! locations. This eliminates the dependence on arbitrary values over land or
                                ! outside of the domain.
HORVISC_BOUND_COEF = 0.8        !   [nondim] default = 0.8
                                ! The nondimensional coefficient of the ratio of the viscosity bounds to the
                                ! theoretical maximum for stability without considering other terms.
USE_KH_BG_2D = False            !   [Boolean] default = False
                                ! If true, read a file containing 2-d background harmonic viscosities. The final
                                ! viscosity is the maximum of the other terms and this background value.
FRICTWORK_BUG = False           !   [Boolean] default = True
                                ! If true, retain an answer-changing bug in calculating the FrictWork, which
                                ! cancels the h in thickness flux and the h at velocity point. This isnot
                                ! recommended.

! === module MOM_vert_friction ===
VERT_FRICTION_ANSWER_DATE = 99991231 ! default = 99991231
                                ! The vintage of the order of arithmetic and expressions in the viscous
                                ! calculations.  Values below 20190101 recover the answers from the end of 2018,
                                ! while higher values use expressions that do not use an arbitrary hard-coded
                                ! maximum viscous coupling coefficient between layers.  Values below 20230601
                                ! recover a form of the viscosity within the mixed layer that breaks up the
                                ! magnitude of the wind stress in some non-Boussinesq cases.
DIRECT_STRESS = False           !   [Boolean] default = False
                                ! If true, the wind stress is distributed over the topmost HMIX_STRESS of fluid
                                ! (like in HYCOM), and an added mixed layer viscosity or a physically based
                                ! boundary layer turbulence parameterization is not needed for stability.
FIXED_DEPTH_LOTW_ML = False     !   [Boolean] default = False
                                ! If true, use a Law-of-the-wall prescription for the mixed layer viscosity
                                ! within a boundary layer that is the lesser of HMIX_FIXED and the total depth
                                ! of the ocean in a column.
LOTW_VISCOUS_ML_FLOOR = False   !   [Boolean] default = False
                                ! If true, use a Law-of-the-wall prescription to set a lower bound on the
                                ! viscous coupling between layers within the surface boundary layer, based the
                                ! distance of interfaces from the surface.  This only acts when there are large
                                ! changes in the thicknesses of successive layers or when the viscosity is set
                                ! externally and the wind stress has subsequently increased.
VON_KARMAN_CONST = 0.41         !   [nondim] default = 0.41
                                ! The value the von Karman constant as used for mixed layer viscosity.
HARMONIC_VISC = False           !   [Boolean] default = False
                                ! If true, use the harmonic mean thicknesses for calculating the vertical
                                ! viscosity.
HARMONIC_BL_SCALE = 0.0         !   [nondim] default = 0.0
                                ! A scale to determine when water is in the boundary layers based solely on
                                ! harmonic mean thicknesses for the purpose of determining the extent to which
                                ! the thicknesses used in the viscosities are upwinded.
HMIX_FIXED = 0.5                !   [m]
                                ! The prescribed depth over which the near-surface viscosity and diffusivity are
                                ! elevated when the bulk mixed layer is not used.
USE_GL90_IN_SSW = False         !   [Boolean] default = False
                                ! If true, use simpler method to calculate 1/N^2 in GL90 vertical viscosity
                                ! coefficient. This method is valid in stacked shallow water mode.
KV_ML_INVZ2 = 0.0               !   [m2 s-1] default = 0.0
                                ! An extra kinematic viscosity in a mixed layer of thickness HMIX_FIXED, with
                                ! the actual viscosity scaling as 1/(z*HMIX_FIXED)^2, where z is the distance
                                ! from the surface, to allow for finite wind stresses to be transmitted through
                                ! infinitesimally thin surface layers.  This is an older option for numerical
                                ! convenience without a strong physical basis, and its use is now discouraged.
MAXVEL = 6.0                    !   [m s-1] default = 3.0E+08
                                ! The maximum velocity allowed before the velocity components are truncated.
CFL_BASED_TRUNCATIONS = True    !   [Boolean] default = True
                                ! If true, base truncations on the CFL number, and not an absolute speed.
CFL_TRUNCATE = 0.5              !   [nondim] default = 0.5
                                ! The value of the CFL number that will cause velocity components to be
                                ! truncated; instability can occur past 0.5.
CFL_REPORT = 0.5                !   [nondim] default = 0.5
                                ! The value of the CFL number that causes accelerations to be reported; the
                                ! default is CFL_TRUNCATE.
CFL_TRUNCATE_RAMP_TIME = 7200.0 !   [s] default = 0.0
                                ! The time over which the CFL truncation value is ramped up at the beginning of
                                ! the run.
CFL_TRUNCATE_START = 0.0        !   [nondim] default = 0.0
                                ! The start value of the truncation CFL number used when ramping up CFL_TRUNC.
STOKES_MIXING_COMBINED = False  !   [Boolean] default = False
                                ! Flag to use Stokes drift Mixing via the Lagrangian  current (Eulerian plus
                                ! Stokes drift).  Still needs work and testing, so not recommended for use.
VEL_UNDERFLOW = 0.0             !   [m s-1] default = 0.0
                                ! A negligibly small velocity magnitude below which velocity components are set
                                ! to 0.  A reasonable value might be 1e-30 m/s, which is less than an Angstrom
                                ! divided by the age of the universe.

! === module MOM_barotropic ===
USE_BT_CONT_TYPE = True         !   [Boolean] default = True
                                ! If true, use a structure with elements that describe effective face areas from
                                ! the summed continuity solver as a function the barotropic flow in coupling
                                ! between the barotropic and baroclinic flow.  This is only used if SPLIT is
                                ! true.
INTEGRAL_BT_CONTINUITY = False  !   [Boolean] default = False
                                ! If true, use the time-integrated velocity over the barotropic steps to
                                ! determine the integrated transports used to update the continuity equation.
                                ! Otherwise the transports are the sum of the transports based on a series of
                                ! instantaneous velocities and the BT_CONT_TYPE for transports.  This is only
                                ! valid if USE_BT_CONT_TYPE = True.
BOUND_BT_CORRECTION = True      !   [Boolean] default = False
                                ! If true, the corrective pseudo mass-fluxes into the barotropic solver are
                                ! limited to values that require less than maxCFL_BT_cont to be accommodated.
BT_CONT_CORR_BOUNDS = True      !   [Boolean] default = True
                                ! If true, and BOUND_BT_CORRECTION is true, use the BT_cont_type variables to
                                ! set limits determined by MAXCFL_BT_CONT on the CFL number of the velocities
                                ! that are likely to be driven by the corrective mass fluxes.
ADJUST_BT_CONT = False          !   [Boolean] default = False
                                ! If true, adjust the curve fit to the BT_cont type that is used by the
                                ! barotropic solver to match the transport about which the flow is being
                                ! linearized.
GRADUAL_BT_ICS = False          !   [Boolean] default = False
                                ! If true, adjust the initial conditions for the barotropic solver to the values
                                ! from the layered solution over a whole timestep instead of instantly. This is
                                ! a decent approximation to the inclusion of sum(u dh_dt) while also correcting
                                ! for truncation errors.
BT_USE_VISC_REM_U_UH0 = False   !   [Boolean] default = False
                                ! If true, use the viscous remnants when estimating the barotropic velocities
                                ! that were used to calculate uh0 and vh0.  False is probably the better choice.
BT_PROJECT_VELOCITY = True      !   [Boolean] default = False
                                ! If true, step the barotropic velocity first and project out the velocity
                                ! tendency by 1+BEBT when calculating the transport.  The default (false) is to
                                ! use a predictor continuity step to find the pressure field, and then to do a
                                ! corrector continuity step using a weighted average of the old and new
                                ! velocities, with weights of (1-BEBT) and BEBT.
BT_NONLIN_STRESS = False        !   [Boolean] default = False
                                ! If true, use the full depth of the ocean at the start of the barotropic step
                                ! when calculating the surface stress contribution to the barotropic
                                ! acclerations.  Otherwise use the depth based on bathyT.
DYNAMIC_SURFACE_PRESSURE = True !   [Boolean] default = False
                                ! If true, add a dynamic pressure due to a viscous ice shelf, for instance.
ICE_LENGTH_DYN_PSURF = 1.0E+04  !   [m] default = 1.0E+04
                                ! The length scale at which the Rayleigh damping rate due to the ice strength
                                ! should be the same as if a Laplacian were applied, if DYNAMIC_SURFACE_PRESSURE
                                ! is true.
DEPTH_MIN_DYN_PSURF = 1.0E-06   !   [m] default = 1.0E-06
                                ! The minimum depth to use in limiting the size of the dynamic surface pressure
                                ! for stability, if DYNAMIC_SURFACE_PRESSURE is true..
CONST_DYN_PSURF = 0.9           !   [nondim] default = 0.9
                                ! The constant that scales the dynamic surface pressure, if
                                ! DYNAMIC_SURFACE_PRESSURE is true.  Stable values are < ~1.0.
BT_CORIOLIS_SCALE = 1.0         !   [nondim] default = 1.0
                                ! A factor by which the barotropic Coriolis anomaly terms are scaled.
BAROTROPIC_ANSWER_DATE = 99991231 ! default = 99991231
                                ! The vintage of the expressions in the barotropic solver. Values below 20190101
                                ! recover the answers from the end of 2018, while higher values use more
                                ! efficient or general expressions.
VISC_REM_BT_WEIGHT_BUG = False  !   [Boolean] default = False
                                ! If true, recover a bug in barotropic solver that uses an unnormalized weight
                                ! function for vertical averages of baroclinic velocity and forcing. Default of
                                ! this flag is set by VISC_REM_BUG.
TIDAL_SAL_FLATHER = False       !   [Boolean] default = False
                                ! If true, then apply adjustments to the external gravity wave speed used with
                                ! the Flather OBC routine consistent with the barotropic solver. This applies to
                                ! cases with  tidal forcing using the scalar self-attraction approximation. The
                                ! default is currently False in order to retain previous answers but should be
                                ! set to True for new experiments
SADOURNY = True                 !   [Boolean] default = True
                                ! If true, the Coriolis terms are discretized with the Sadourny (1975) energy
                                ! conserving scheme, otherwise the Arakawa & Hsu scheme is used.  If the
                                ! internal deformation radius is not resolved, the Sadourny scheme should
                                ! probably be used.
BT_THICK_SCHEME = "FROM_BT_CONT" ! default = "FROM_BT_CONT"
                                ! A string describing the scheme that is used to set the open face areas used
                                ! for barotropic transport and the relative weights of the accelerations. Valid
                                ! values are:
                                !    ARITHMETIC - arithmetic mean layer thicknesses
                                !    HARMONIC - harmonic mean layer thicknesses
                                !    HYBRID (the default) - use arithmetic means for
                                !       layers above the shallowest bottom, the harmonic
                                !       mean for layers below, and a weighted average for
                                !       layers that straddle that depth
                                !    FROM_BT_CONT - use the average thicknesses kept
                                !       in the h_u and h_v fields of the BT_cont_type
BT_STRONG_DRAG = False          !   [Boolean] default = False
                                ! If true, use a stronger estimate of the retarding effects of strong bottom
                                ! drag, by making it implicit with the barotropic time-step instead of implicit
                                ! with the baroclinic time-step and dividing by the number of barotropic steps.
BT_LINEAR_WAVE_DRAG = False     !   [Boolean] default = False
                                ! If true, apply a linear drag to the barotropic velocities, using rates set by
                                ! lin_drag_u & _v divided by the depth of the ocean.  This was introduced to
                                ! facilitate tide modeling.
CLIP_BT_VELOCITY = False        !   [Boolean] default = False
                                ! If true, limit any velocity components that exceed CFL_TRUNCATE.  This should
                                ! only be used as a desperate debugging measure.
MAXCFL_BT_CONT = 0.25           !   [nondim] default = 0.25
                                ! The maximum permitted CFL number associated with the barotropic accelerations
                                ! from the summed velocities times the time-derivatives of thicknesses.
DT_BT_FILTER = -0.25            !   [sec or nondim] default = -0.25
                                ! A time-scale over which the barotropic mode solutions are filtered, in seconds
                                ! if positive, or as a fraction of DT if negative. When used this can never be
                                ! taken to be longer than 2*dt.  Set this to 0 to apply no filtering.
G_BT_EXTRA = 0.0                !   [nondim] default = 0.0
                                ! A nondimensional factor by which gtot is enhanced.
SSH_EXTRA = 10.0                !   [m] default = 10.0
                                ! An estimate of how much higher SSH might get, for use in calculating the safe
                                ! external wave speed. The default is the minimum of 10 m or 5% of
                                ! MAXIMUM_DEPTH.
LINEARIZED_BT_CORIOLIS = True   !   [Boolean] default = True
                                ! If true use the bottom depth instead of the total water column thickness in
                                ! the barotropic Coriolis term calculations.
BEBT = 0.2                      !   [nondim] default = 0.1
                                ! BEBT determines whether the barotropic time stepping uses the forward-backward
                                ! time-stepping scheme or a backward Euler scheme. BEBT is valid in the range
                                ! from 0 (for a forward-backward treatment of nonrotating gravity waves) to 1
                                ! (for a backward Euler treatment). In practice, BEBT must be greater than about
                                ! 0.05.
DTBT = -0.9                     !   [s or nondim] default = -0.98
                                ! The barotropic time step, in s. DTBT is only used with the split explicit time
                                ! stepping. To set the time step automatically based the maximum stable value
                                ! use 0, or a negative value gives the fraction of the stable value. Setting
                                ! DTBT to 0 is the same as setting it to -0.98. The value of DTBT that will
                                ! actually be used is an integer fraction of DT, rounding down.
BT_USE_OLD_CORIOLIS_BRACKET_BUG = False !   [Boolean] default = False
                                ! If True, use an order of operations that is not bitwise rotationally symmetric
                                ! in the meridional Coriolis term of the barotropic solver.

! === module MOM_mixed_layer_restrat ===
MIXEDLAYER_RESTRAT = True       !   [Boolean] default = False
                                ! If true, a density-gradient dependent re-stratifying flow is imposed in the
                                ! mixed layer. Can be used in ALE mode without restriction but in layer mode can
                                ! only be used if BULKMIXEDLAYER is true.
MLE%
USE_BODNER23 = True             !   [Boolean] default = False
                                ! If true, use the Bodner et al., 2023, formulation of the re-stratifying
                                ! mixed-layer restratification parameterization. This only works in ALE mode.
CR = 0.0175                     !   [nondim] default = 0.0
                                ! The efficiency coefficient in eq 27 of Bodner et al., 2023.
BODNER_NSTAR = 0.066            !   [nondim] default = 0.066
                                ! The n* value used to estimate the turbulent vertical momentum flux in Bodner
                                ! et al., 2023, eq. 18. This is independent of the value used in the PBL scheme
                                ! but should be set to be the same for consistency.
BODNER_MSTAR = 0.5              !   [nondim] default = 0.5
                                ! The m* value used to estimate the turbulent vertical momentum flux in Bodner
                                ! et al., 2023, eq. 18. This is independent of the value used in the PBL scheme
                                ! but should be set to be the same for consistency.
BLD_GROWING_TFILTER = 0.0       !   [s] default = 0.0
                                ! The time-scale for a running-mean filter applied to the boundary layer depth
                                ! (BLD) when the BLD is deeper than the running mean. A value of 0
                                ! instantaneously sets the running mean to the current value of BLD.
BLD_DECAYING_TFILTER = 8.64E+04 !   [s] default = 0.0
                                ! The time-scale for a running-mean filter applied to the boundary layer depth
                                ! (BLD) when the BLD is shallower than the running mean. A value of 0
                                ! instantaneously sets the running mean to the current value of BLD.
MLD_GROWING_TFILTER = 0.0       !   [s] default = 0.0
                                ! The time-scale for a running-mean filter applied to the time-filtered BLD,
                                ! when the latter is deeper than the running mean. A value of 0 instantaneously
                                ! sets the running mean to the current value filtered BLD.
MLD_DECAYING_TFILTER = 2.592E+06 !   [s] default = 0.0
                                ! The time-scale for a running-mean filter applied to the time-filtered BLD,
                                ! when the latter is shallower than the running mean. A value of 0
                                ! instantaneously sets the running mean to the current value filtered BLD.
ML_RESTRAT_ANSWER_DATE = 99991231 ! default = 99991231
                                ! The vintage of the order of arithmetic and expressions in the mixed layer
                                ! restrat calculations.  Values below 20240201 recover the answers from the end
                                ! of 2023, while higher values use the new cuberoot function in the Bodner code
                                ! to avoid needing to undo dimensional rescaling.
MIN_WSTAR2 = 1.0E-09            !   [m2 s-2] default = 1.0E-24
                                ! The minimum lower bound to apply to the vertical momentum flux, w'u', in the
                                ! Bodner et al., restratification parameterization. This avoids a
                                ! division-by-zero in the limit when u* and the buoyancy flux are zero.  The
                                ! default is less than the molecular viscosity of water times the Coriolis
                                ! parameter a micron away from the equator.
TAIL_DH = 0.0                   !   [nondim] default = 0.0
                                ! Fraction by which to extend the mixed-layer restratification depth used for a
                                ! smoother stream function at the base of the mixed-layer.
USE_STANLEY_TVAR = False        !   [Boolean] default = False
                                ! If true, turn on Stanley SGS T variance parameterization in ML restrat code.
USE_CR_GRID = False             !   [Boolean] default = False
                                ! If true, read in a spatially varying Cr field.
USE_MLD_GRID = False            !   [Boolean] default = False
                                ! If true, read in a spatially varying MLD_decaying_Tfilt field.
%MLE
MLE_USE_PBL_MLD = True          !   [Boolean] default = False
                                ! If true, the MLE parameterization will use the mixed-layer depth provided by
                                ! the active PBL parameterization. If false, MLE will estimate a MLD based on a
                                ! density difference with the surface using the parameter MLE_DENSITY_DIFF.

! === module MOM_diagnostics ===
DIAG_EBT_MONO_N2_COLUMN_FRACTION = 0.0 !   [nondim] default = 0.0
                                ! The lower fraction of water column over which N2 is limited as monotonic for
                                ! the purposes of calculating the equivalent barotropic wave speed.
DIAG_EBT_MONO_N2_DEPTH = -1.0   !   [m] default = -1.0
                                ! The depth below which N2 is limited as monotonic for the purposes of
                                ! calculating the equivalent barotropic wave speed.
INTWAVE_REMAPPING_USE_OM4_SUBCELLS = False !   [Boolean] default = True
                                ! If true, use the OM4 remapping-via-subcells algorithm for calculating EBT
                                ! structure. See REMAPPING_USE_OM4_SUBCELLS for details. We recommend setting
                                ! this option to false.

! === module MOM_diabatic_driver ===
! The following parameters are used for diabatic processes.
USE_LEGACY_DIABATIC_DRIVER = False !   [Boolean] default = True
                                ! If true, use a legacy version of the diabatic subroutine. This is temporary
                                ! and is needed to avoid change in answers.
ENERGETICS_SFC_PBL = True       !   [Boolean] default = False
                                ! If true, use an implied energetics planetary boundary layer scheme to
                                ! determine the diffusivity and viscosity in the surface boundary layer.
EPBL_IS_ADDITIVE = False        !   [Boolean] default = True
                                ! If true, the diffusivity from ePBL is added to all other diffusivities.
                                ! Otherwise, the larger of kappa-shear and ePBL diffusivities are used.
PRANDTL_EPBL = 1.0              !   [nondim] default = 1.0
                                ! The Prandtl number used by ePBL to convert vertical diffusivities into
                                ! viscosities.
INTERNAL_TIDES = False          !   [Boolean] default = False
                                ! If true, use the code that advances a separate set of equations for the
                                ! internal tide energy density.
MASSLESS_MATCH_TARGETS = True   !   [Boolean] default = True
                                ! If true, the temperature and salinity of massless layers are kept consistent
                                ! with their target densities. Otherwise the properties of massless layers
                                ! evolve diffusively to match massive neighboring layers.
AGGREGATE_FW_FORCING = True     !   [Boolean] default = True
                                ! If true, the net incoming and outgoing fresh water fluxes are combined and
                                ! applied as either incoming or outgoing depending on the sign of the net. If
                                ! false, the net incoming fresh water flux is added to the model and thereafter
                                ! the net outgoing is removed from the topmost non-vanished layers of the
                                ! updated state.
MIX_BOUNDARY_TRACERS = True     !   [Boolean] default = True
                                ! If true, mix the passive tracers in massless layers at the bottom into the
                                ! interior as though a diffusivity of KD_MIN_TR were operating.
MIX_BOUNDARY_TRACER_ALE = False !   [Boolean] default = False
                                ! If true and in ALE mode, mix the passive tracers in massless layers at the
                                ! bottom into the interior as though a diffusivity of KD_MIN_TR were operating.
KD_MIN_TR = 1.5E-06             !   [m2 s-1] default = 1.5E-06
                                ! A minimal diffusivity that should always be applied to tracers, especially in
                                ! massless layers near the bottom. The default is 0.1*KD.
KD_BBL_TR = 0.0                 !   [m2 s-1] default = 0.0
                                ! A bottom boundary layer tracer diffusivity that will allow for explicitly
                                ! specified bottom fluxes. The entrainment at the bottom is at least
                                ! sqrt(Kd_BBL_tr*dt) over the same distance.
TRACER_TRIDIAG = False          !   [Boolean] default = False
                                ! If true, use the passive tracer tridiagonal solver for T and S
MINIMUM_FORCING_DEPTH = 0.001   !   [m] default = 0.001
                                ! The smallest depth over which forcing can be applied. This only takes effect
                                ! when near-surface layers become thin relative to this scale, in which case the
                                ! forcing tendencies scaled down by distributing the forcing over this depth
                                ! scale.
EVAP_CFL_LIMIT = 0.8            !   [nondim] default = 0.8
                                ! The largest fraction of a layer than can be lost to forcing (e.g. evaporation,
                                ! sea-ice formation) in one time-step. The unused mass loss is passed down
                                ! through the column.
MLD_EN_VALS = 3*0.0             !   [J/m2] default = 0.0
                                ! The energy values used to compute MLDs.  If not set (or all set to 0.), the
                                ! default will overwrite to 25., 2500., 250000.
HREF_FOR_MLD = 0.0              !   [m] default = 0.0
                                ! Reference depth used to calculate the potential density used to find the mixed
                                ! layer depth based on a delta rho = 0.03 kg/m3.
DIAG_MLD_DENSITY_DIFF = 0.1     !   [kg/m3] default = 0.1
                                ! The density difference used to determine a diagnostic mixed layer depth,
                                ! MLD_user, following the definition of Levitus 1982. The MLD is the depth at
                                ! which the density is larger than the surface density by the specified amount.
DIAG_DEPTH_SUBML_N2 = 50.0      !   [m] default = 50.0
                                ! The distance over which to calculate a diagnostic of the stratification at the
                                ! base of the mixed layer.

! === module MOM_CVMix_KPP ===
! This is the MOM wrapper to CVMix:KPP
! See http://cvmix.github.io/
USE_KPP = False                 !   [Boolean] default = False
                                ! If true, turns on the [CVMix] KPP scheme of Large et al., 1994, to calculate
                                ! diffusivities and non-local transport in the OBL.

! === module MOM_CVMix_conv ===
! Parameterization of enhanced mixing due to convection via CVMix
USE_CVMix_CONVECTION = False    !   [Boolean] default = False
                                ! If true, turns on the enhanced mixing due to convection via CVMix. This scheme
                                ! increases diapycnal diffs./viscs. at statically unstable interfaces. Relevant
                                ! parameters are contained in the CVMix_CONVECTION% parameter block.

! === module MOM_set_diffusivity ===
FLUX_RI_MAX = 0.2               !   [nondim] default = 0.2
                                ! The flux Richardson number where the stratification is large enough that N2 >
                                ! omega2.  The full expression for the Flux Richardson number is usually
                                ! FLUX_RI_MAX*N2/(N2+OMEGA2).
SET_DIFF_ANSWER_DATE = 99991231 ! default = 99991231
                                ! The vintage of the order of arithmetic and expressions in the set diffusivity
                                ! calculations.  Values below 20190101 recover the answers from the end of 2018,
                                ! while higher values use updated and more robust forms of the same expressions.

! === module MOM_tidal_mixing ===
! Vertical Tidal Mixing Parameterization
USE_CVMix_TIDAL = False         !   [Boolean] default = False
                                ! If true, turns on tidal mixing via CVMix
INT_TIDE_DISSIPATION = True     !   [Boolean] default = False
                                ! If true, use an internal tidal dissipation scheme to drive diapycnal mixing,
                                ! along the lines of St. Laurent et al. (2002) and Simmons et al. (2004).
TIDAL_MIXING_ANSWER_DATE = 99991231 ! default = 99991231
                                ! The vintage of the order of arithmetic and expressions in the tidal mixing
                                ! calculations.  Values below 20190101 recover the answers from the end of 2018,
                                ! while higher values use updated and more robust forms of the same expressions.
INT_TIDE_PROFILE = "POLZIN_09"  ! default = "STLAURENT_02"
                                ! INT_TIDE_PROFILE selects the vertical profile of energy dissipation with
                                ! INT_TIDE_DISSIPATION. Valid values are:
                                !    STLAURENT_02 - Use the St. Laurent et al exponential
                                !                   decay profile.
                                !    POLZIN_09 - Use the Polzin WKB-stretched algebraic
                                !                   decay profile.
LEE_WAVE_DISSIPATION = False    !   [Boolean] default = False
                                ! If true, use an lee wave driven dissipation scheme to drive diapycnal mixing,
                                ! along the lines of Nikurashin (2010) and using the St. Laurent et al. (2002)
                                ! and Simmons et al. (2004) vertical profile
INT_TIDE_LOWMODE_DISSIPATION = False !   [Boolean] default = False
                                ! If true, consider mixing due to breaking low modes that have been remotely
                                ! generated; as with itidal drag on the barotropic tide, use an internal tidal
                                ! dissipation scheme to drive diapycnal mixing, along the lines of St. Laurent
                                ! et al. (2002) and Simmons et al. (2004).
NU_POLZIN = 0.0697              !   [nondim] default = 0.0697
                                ! When the Polzin decay profile is used, this is a non-dimensional constant in
                                ! the expression for the vertical scale of decay for the tidal energy
                                ! dissipation.
NBOTREF_POLZIN = 9.61E-04       !   [s-1] default = 9.61E-04
                                ! When the Polzin decay profile is used, this is the reference value of the
                                ! buoyancy frequency at the ocean bottom in the Polzin formulation for the
                                ! vertical scale of decay for the tidal energy dissipation.
POLZIN_DECAY_SCALE_FACTOR = 1.0 !   [nondim] default = 1.0
                                ! When the Polzin decay profile is used, this is a scale factor for the vertical
                                ! scale of decay of the tidal energy dissipation.
POLZIN_SCALE_MAX_FACTOR = 1.0   !   [nondim] default = 1.0
                                ! When the Polzin decay profile is used, this is a factor to limit the vertical
                                ! scale of decay of the tidal energy dissipation to
                                ! POLZIN_DECAY_SCALE_MAX_FACTOR times the depth of the ocean.
POLZIN_MIN_DECAY_SCALE = 0.0    !   [m] default = 0.0
                                ! When the Polzin decay profile is used, this is the minimum vertical decay
                                ! scale for the vertical profile
                                ! of internal tide dissipation with the Polzin (2009) formulation
INT_TIDE_DECAY_SCALE = 300.3003003003003 !   [m] default = 500.0
                                ! The decay scale away from the bottom for tidal TKE with the new coding when
                                ! INT_TIDE_DISSIPATION is used.
MU_ITIDES = 0.2                 !   [nondim] default = 0.2
                                ! A dimensionless turbulent mixing efficiency used with INT_TIDE_DISSIPATION,
                                ! often 0.2.
GAMMA_ITIDES = 0.3333           !   [nondim] default = 0.3333
                                ! The fraction of the internal tidal energy that is dissipated locally with
                                ! INT_TIDE_DISSIPATION. THIS NAME COULD BE BETTER.
MIN_ZBOT_ITIDES = 0.0           !   [m] default = 0.0
                                ! Turn off internal tidal dissipation when the total ocean depth is less than
                                ! this value.
KAPPA_ITIDES = 6.28319E-04      !   [m-1] default = 6.283185307179586E-04
                                ! A topographic wavenumber used with INT_TIDE_DISSIPATION. The default is 2pi/10
                                ! km, as in St.Laurent et al. 2002.
UTIDE = 0.0                     !   [m s-1] default = 0.0
                                ! The constant tidal amplitude used with INT_TIDE_DISSIPATION.
KAPPA_H2_FACTOR = 0.84          !   [nondim] default = 1.0
                                ! A scaling factor for the roughness amplitude with INT_TIDE_DISSIPATION.
TKE_ITIDE_MAX = 0.1             !   [W m-2] default = 1000.0
                                ! The maximum internal tide energy source available to mix above the bottom
                                ! boundary layer with INT_TIDE_DISSIPATION.
READ_TIDEAMP = True             !   [Boolean] default = False
                                ! If true, read a file (given by TIDEAMP_FILE) containing the tidal amplitude
                                ! with INT_TIDE_DISSIPATION.
TIDEAMP_FILE = "tideamp.nc"     ! default = "tideamp.nc"
                                ! The path to the file containing the spatially varying tidal amplitudes with
                                ! INT_TIDE_DISSIPATION.
TIDEAMP_VARNAME = "tideamp"     ! default = "tideamp"
                                ! The name of the tidal amplitude variable in the input file.
H2_FILE = "bottom_roughness.nc" !
                                ! The path to the file containing the sub-grid-scale topographic roughness
                                ! amplitude with INT_TIDE_DISSIPATION.
ROUGHNESS_VARNAME = "h2"        ! default = "h2"
                                ! The name in the input file of the squared sub-grid-scale topographic roughness
                                ! amplitude variable.
FRACTIONAL_ROUGHNESS_MAX = 0.1  !   [nondim] default = 0.1
                                ! The maximum topographic roughness amplitude as a fraction of the mean depth,
                                ! or a negative value for no limitations on roughness.
ML_RADIATION = False            !   [Boolean] default = False
                                ! If true, allow a fraction of TKE available from wind work to penetrate below
                                ! the base of the mixed layer with a vertical decay scale determined by the
                                ! minimum of: (1) The depth of the mixed layer, (2) an Ekman length scale.
BBL_EFFIC = 0.01                !   [nondim] default = 0.2
                                ! The efficiency with which the energy extracted by bottom drag drives BBL
                                ! diffusion.  This is only used if BOTTOMDRAGLAW is true.
BBL_MIXING_MAX_DECAY = 200.0    !   [m] default = 200.0
                                ! The maximum decay scale for the BBL diffusion, or 0 to allow the mixing to
                                ! penetrate as far as stratification and rotation permit.  The default for now
                                ! is 200 m. This is only used if BOTTOMDRAGLAW is true.
BBL_MIXING_AS_MAX = False       !   [Boolean] default = True
                                ! If true, take the maximum of the diffusivity from the BBL mixing and the other
                                ! diffusivities. Otherwise, diffusivity from the BBL_mixing is simply added.
USE_LOTW_BBL_DIFFUSIVITY = True !   [Boolean] default = False
                                ! If true, uses a simple, imprecise but non-coordinate dependent, model of BBL
                                ! mixing diffusivity based on Law of the Wall. Otherwise, uses the original BBL
                                ! scheme.
LOTW_BBL_USE_OMEGA = True       !   [Boolean] default = True
                                ! If true, use the maximum of Omega and N for the TKE to diffusion calculation.
                                ! Otherwise, N is N.
VON_KARMAN_BBL = 0.41           !   [nondim] default = 0.41
                                ! The value the von Karman constant as used in calculating the BBL diffusivity.
LOTW_BBL_ANSWER_DATE = 20190101 ! default = 20190101
                                ! The vintage of the order of arithmetic and expressions in the LOTW_BBL
                                ! calculations.  Values below 20240630 recover the original answers, while
                                ! higher values use more accurate expressions.  This only applies when
                                ! USE_LOTW_BBL_DIFFUSIVITY is true.
DZ_BBL_AVG_MIN = 0.0            !   [m] default = 0.0
                                ! A minimal distance over which to average to determine the average bottom
                                ! boundary layer density.
SIMPLE_TKE_TO_KD = True         !   [Boolean] default = False
                                ! If true, uses a simple estimate of Kd/TKE that will work for arbitrary
                                ! vertical coordinates. If false, calculates Kd/TKE and bounds based on exact
                                ! energetics for an isopycnal layer-formulation.

! === module MOM_bkgnd_mixing ===
! Adding static vertical background mixing coefficients
KD = 1.5E-05                    !   [m2 s-1] default = 0.0
                                ! The background diapycnal diffusivity of density in the interior. Zero or the
                                ! molecular value, ~1e-7 m2 s-1, may be used.
KD_MIN = 2.0E-06                !   [m2 s-1] default = 1.5E-07
                                ! The minimum diapycnal diffusivity.
BRYAN_LEWIS_DIFFUSIVITY = False !   [Boolean] default = False
                                ! If true, use a Bryan & Lewis (JGR 1979) like tanh profile of background
                                ! diapycnal diffusivity with depth. This is done via CVMix.
HORIZ_VARYING_BACKGROUND = False !   [Boolean] default = False
                                ! If true, apply vertically uniform, latitude-dependent background diffusivity,
                                ! as described in Danabasoglu et al., 2012
PRANDTL_BKGND = 1.0             !   [nondim] default = 1.0
                                ! Turbulent Prandtl number used to convert vertical background diffusivities
                                ! into viscosities.
HENYEY_IGW_BACKGROUND = True    !   [Boolean] default = False
                                ! If true, use a latitude-dependent scaling for the near surface background
                                ! diffusivity, as described in Harrison & Hallberg, JPO 2008.
HENYEY_N0_2OMEGA = 20.0         !   [nondim] default = 20.0
                                ! The ratio of the typical Buoyancy frequency to twice the Earth's rotation
                                ! period, used with the Henyey scaling from the mixing.
HENYEY_MAX_LAT = 73.0           !   [degN] default = 95.0
                                ! A latitude poleward of which the Henyey profile is returned to the minimum
                                ! diffusivity
KD_TANH_LAT_FN = False          !   [Boolean] default = False
                                ! If true, use a tanh dependence of Kd_sfc on latitude, like CM2.1/CM2M.  There
                                ! is no physical justification for this form, and it can not be used with
                                ! HENYEY_IGW_BACKGROUND.
KD_MAX = 0.1                    !   [m2 s-1] default = -1.0
                                ! The maximum permitted increment for the diapycnal diffusivity from TKE-based
                                ! parameterizations, or a negative value for no limit.
KD_ADD = 0.0                    !   [m2 s-1] default = 0.0
                                ! A uniform diapycnal diffusivity that is added everywhere without any filtering
                                ! or scaling.
USER_CHANGE_DIFFUSIVITY = False !   [Boolean] default = False
                                ! If true, call user-defined code to change the diffusivity.
DISSIPATION_MIN = 0.0           !   [W m-3] default = 0.0
                                ! The minimum dissipation by which to determine a lower bound of Kd (a floor).
DISSIPATION_N0 = 0.0            !   [W m-3] default = 0.0
                                ! The intercept when N=0 of the N-dependent expression used to set a minimum
                                ! dissipation by which to determine a lower bound of Kd (a floor): A in eps_min
                                ! = A + B*N.
DISSIPATION_N1 = 0.0            !   [J m-3] default = 0.0
                                ! The coefficient multiplying N, following Gargett, used to set a minimum
                                ! dissipation by which to determine a lower bound of Kd (a floor): B in eps_min
                                ! = A + B*N
DISSIPATION_KD_MIN = 0.0        !   [m2 s-1] default = 0.0
                                ! The minimum vertical diffusivity applied as a floor.
DOUBLE_DIFFUSION = True         !   [Boolean] default = False
                                ! If true, increase diffusivites for temperature or salinity based on the
                                ! double-diffusive parameterization described in Large et al. (1994).
MAX_RRHO_SALT_FINGERS = 2.55    !   [nondim] default = 1.9
                                ! Maximum density ratio for salt fingering regime.
MAX_SALT_DIFF_SALT_FINGERS = 1.0E-04 !   [m2 s-1] default = 1.0E-04
                                ! Maximum salt diffusivity for salt fingering regime.
KV_MOLECULAR = 1.5E-06          !   [m2 s-1] default = 1.5E-06
                                ! Molecular viscosity for calculation of fluxes under double-diffusive
                                ! convection.

! === module MOM_kappa_shear ===
! Parameterization of shear-driven turbulence following Jackson, Hallberg and Legg, JPO 2008
USE_JACKSON_PARAM = True        !   [Boolean] default = False
                                ! If true, use the Jackson-Hallberg-Legg (JPO 2008) shear mixing
                                ! parameterization.
VERTEX_SHEAR = True             !   [Boolean] default = False
                                ! If true, do the calculations of the shear-driven mixing at the cell vertices
                                ! (i.e., the vorticity points).
RINO_CRIT = 0.25                !   [nondim] default = 0.25
                                ! The critical Richardson number for shear mixing.
SHEARMIX_RATE = 0.089           !   [nondim] default = 0.089
                                ! A nondimensional rate scale for shear-driven entrainment. Jackson et al find
                                ! values in the range of 0.085-0.089.
MAX_RINO_IT = 25                !   [nondim] default = 50
                                ! The maximum number of iterations that may be used to estimate the Richardson
                                ! number driven mixing.
KD_KAPPA_SHEAR_0 = 1.5E-05      !   [m2 s-1] default = 1.5E-05
                                ! The background diffusivity that is used to smooth the density and shear
                                ! profiles before solving for the diffusivities.  The default is the greater of
                                ! KD and 1e-7 m2 s-1.
KD_SEED_KAPPA_SHEAR = 1.0       !   [m2 s-1] default = 1.0
                                ! A moderately large seed value of diapycnal diffusivity that is used as a
                                ! starting turbulent diffusivity in the iterations to find an energetically
                                ! constrained solution for the shear-driven diffusivity.
KD_TRUNC_KAPPA_SHEAR = 1.5E-07  !   [m2 s-1] default = 1.5E-07
                                ! The value of shear-driven diffusivity that is considered negligible and is
                                ! rounded down to 0. The default is 1% of KD_KAPPA_SHEAR_0.
FRI_CURVATURE = -0.97           !   [nondim] default = -0.97
                                ! The nondimensional curvature of the function of the Richardson number in the
                                ! kappa source term in the Jackson et al. scheme.
TKE_N_DECAY_CONST = 0.24        !   [nondim] default = 0.24
                                ! The coefficient for the decay of TKE due to stratification (i.e. proportional
                                ! to N*tke). The values found by Jackson et al. are 0.24-0.28.
TKE_SHEAR_DECAY_CONST = 0.14    !   [nondim] default = 0.14
                                ! The coefficient for the decay of TKE due to shear (i.e. proportional to
                                ! |S|*tke). The values found by Jackson et al. are 0.14-0.12.
KAPPA_BUOY_SCALE_COEF = 0.82    !   [nondim] default = 0.82
                                ! The coefficient for the buoyancy length scale in the kappa equation.  The
                                ! values found by Jackson et al. are in the range of 0.81-0.86.
KAPPA_N_OVER_S_SCALE_COEF2 = 0.0 !   [nondim] default = 0.0
                                ! The square of the ratio of the coefficients of the buoyancy and shear scales
                                ! in the diffusivity equation, Set this to 0 (the default) to eliminate the
                                ! shear scale. This is only used if USE_JACKSON_PARAM is true.
LZ_RESCALE = 1.0                !   [nondim] default = 1.0
                                ! A coefficient to rescale the distance to the nearest solid boundary. This
                                ! adjustment is to account for regions where 3 dimensional turbulence prevents
                                ! the growth of shear instabilies [nondim].
KAPPA_SHEAR_TOL_ERR = 0.1       !   [nondim] default = 0.1
                                ! The fractional error in kappa that is tolerated. Iteration stops when changes
                                ! between subsequent iterations are smaller than this everywhere in a column.
                                ! The peak diffusivities usually converge most rapidly, and have much smaller
                                ! errors than this.
TKE_BACKGROUND = 0.0            !   [m2 s-2] default = 0.0
                                ! A background level of TKE used in the first iteration of the kappa equation.
                                ! TKE_BACKGROUND could be 0.
KAPPA_SHEAR_ELIM_MASSLESS = True !   [Boolean] default = True
                                ! If true, massless layers are merged with neighboring massive layers in this
                                ! calculation.  The default is true and I can think of no good reason why it
                                ! should be false. This is only used if USE_JACKSON_PARAM is true.
MAX_KAPPA_SHEAR_IT = 13         ! default = 13
                                ! The maximum number of iterations that may be used to estimate the
                                ! time-averaged diffusivity.
KAPPA_SHEAR_MAX_KAP_SRC_CHG = 10.0 !   [nondim] default = 10.0
                                ! The maximum permitted increase in the kappa source within an iteration
                                ! relative to the local source; this must be greater than 1.  The lower limit
                                ! for the permitted fractional decrease is (1 - 0.5/kappa_src_max_chg).  These
                                ! limits could perhaps be made dynamic with an improved iterative solver.
KAPPA_SHEAR_VERTEX_PSURF_BUG = False !   [Boolean] default = False
                                ! If true, do a simple average of the cell surface pressures to get a pressure
                                ! at the corner if VERTEX_SHEAR=True.  Otherwise mask out any land points in the
                                ! average.
KAPPA_SHEAR_ITER_BUG = False    !   [Boolean] default = False
                                ! If true, use an older, dimensionally inconsistent estimate of the derivative
                                ! of diffusivity with energy in the Newton's method iteration.  The bug causes
                                ! undercorrections when dz > 1 m.
KAPPA_SHEAR_ALL_LAYER_TKE_BUG = False !   [Boolean] default = False
                                ! If true, report back the latest estimate of TKE instead of the time average
                                ! TKE when there is mass in all layers.  Otherwise always report the time
                                ! averaged TKE, as is currently done when there are some massless layers.
USE_RESTRICTIVE_TOLERANCE_CHECK = True !   [Boolean] default = False
                                ! If true, uses the more restrictive tolerance check to determine if a timestep
                                ! is acceptable for the KS_it outer iteration loop.  False uses the original
                                ! less restrictive check.

! === module MOM_CVMix_shear ===
! Parameterization of shear-driven turbulence via CVMix (various options)
USE_LMD94 = False               !   [Boolean] default = False
                                ! If true, use the Large-McWilliams-Doney (JGR 1994) shear mixing
                                ! parameterization.
USE_PP81 = False                !   [Boolean] default = False
                                ! If true, use the Pacanowski and Philander (JPO 1981) shear mixing
                                ! parameterization.

! === module MOM_CVMix_ddiff ===
! Parameterization of mixing due to double diffusion processes via CVMix
USE_CVMIX_DDIFF = False         !   [Boolean] default = False
                                ! If true, turns on double diffusive processes via CVMix. Note that double
                                ! diffusive processes on viscosity are ignored in CVMix, see
                                ! http://cvmix.github.io/ for justification.

! === module MOM_diabatic_aux ===
! The following parameters are used for auxiliary diabatic processes.
RECLAIM_FRAZIL = True           !   [Boolean] default = True
                                ! If true, try to use any frazil heat deficit to cool any overlying layers down
                                ! to the freezing point, thereby avoiding the creation of thin ice when the SST
                                ! is above the freezing point.
SALT_EXTRACTION_LIMIT = 0.9999  !   [nondim] default = 0.9999
                                ! An upper limit on the fraction of the salt in a layer that can be lost to the
                                ! net surface salt fluxes within a timestep.
PRESSURE_DEPENDENT_FRAZIL = True !   [Boolean] default = False
                                ! If true, use a pressure dependent freezing temperature when making frazil. The
                                ! default is false, which will be faster but is inappropriate with ice-shelf
                                ! cavities.
IGNORE_FLUXES_OVER_LAND = False !   [Boolean] default = False
                                ! If true, the model does not check if fluxes are being applied over land
                                ! points. This is needed when the ocean is coupled with ice shelves and sea ice,
                                ! since the sea ice mask needs to be different than the ocean mask to avoid sea
                                ! ice formation under ice shelves. This flag only works when use_ePBL = True.
DO_RIVERMIX = False             !   [Boolean] default = False
                                ! If true, apply additional mixing wherever there is runoff, so that it is mixed
                                ! down to RIVERMIX_DEPTH if the ocean is that deep.
USE_RIVER_HEAT_CONTENT = False  !   [Boolean] default = False
                                ! If true, use the fluxes%runoff_Hflx field to set the heat carried by runoff,
                                ! instead of using SST*CP*liq_runoff.
USE_CALVING_HEAT_CONTENT = False !   [Boolean] default = False
                                ! If true, use the fluxes%calving_Hflx field to set the heat carried by runoff,
                                ! instead of using SST*CP*froz_runoff.
DO_BRINE_PLUME = False          !   [Boolean] default = False
                                ! If true, use a brine plume parameterization from Nguyen et al., 2009.
VAR_PEN_SW = False              !   [Boolean] default = False
                                ! If true, use one of the CHL_A schemes specified by OPACITY_SCHEME to determine
                                ! the e-folding depth of incoming short wave radiation.

! === module MOM_energetic_PBL ===
ML_OMEGA_FRAC = 0.001           !   [nondim] default = 0.0
                                ! When setting the decay scale for turbulence, use this fraction of the absolute
                                ! rotation rate blended with the local value of f, as sqrt((1-of)*f^2 +
                                ! of*4*omega^2).
EKMAN_SCALE_COEF = 1.0          !   [nondim] default = 1.0
                                ! A nondimensional scaling factor controlling the inhibition of the diffusive
                                ! length scale by rotation. Making this larger decreases the PBL diffusivity.
EPBL_ANSWER_DATE = 99991231     ! default = 99991231
                                ! The vintage of the order of arithmetic and expressions in the energetic PBL
                                ! calculations.  Values below 20190101 recover the answers from the end of 2018,
                                ! while higher values use updated and more robust forms of the same expressions.
                                ! Values below 20240101 use A**(1./3.) to estimate the cube root of A in several
                                ! expressions, while higher values use the integer root function cuberoot(A) and
                                ! therefore can work with scaled variables.
EPBL_ORIGINAL_PE_CALC = True    !   [Boolean] default = True
                                ! If true, the ePBL code uses the original form of the potential energy change
                                ! code.  Otherwise, the newer version that can work with successive increments
                                ! to the diffusivity in upward or downward passes is used.
MKE_TO_TKE_EFFIC = 0.0          !   [nondim] default = 0.0
                                ! The efficiency with which mean kinetic energy released by mechanically forced
                                ! entrainment of the mixed layer is converted to turbulent kinetic energy.
TKE_DECAY = 0.01                !   [nondim] default = 2.5
                                ! TKE_DECAY relates the vertical rate of decay of the TKE available for
                                ! mechanical entrainment to the natural Ekman depth.
EPBL_MSTAR_SCHEME = "OM4"       ! default = "CONSTANT"
                                ! EPBL_MSTAR_SCHEME selects the method for setting mstar.  Valid values are:
                                !    CONSTANT   - Use a fixed mstar given by MSTAR
                                !    OM4        - Use L_Ekman/L_Obukhov in the stabilizing limit, as in OM4
                                !    REICHL_H18 - Use the scheme documented in Reichl & Hallberg, 2018.
MSTAR_CAP = 1.25                !   [nondim] default = -1.0
                                ! If this value is positive, it sets the maximum value of mstar allowed in ePBL.
                                ! (This is not used if EPBL_MSTAR_SCHEME = CONSTANT).
MSTAR2_COEF1 = 0.29             !   [nondim] default = 0.3
                                ! Coefficient in computing mstar when rotation and stabilizing effects are both
                                ! important (used if EPBL_MSTAR_SCHEME = OM4).
MSTAR2_COEF2 = 0.152            !   [nondim] default = 0.085
                                ! Coefficient in computing mstar when only rotation limits the total mixing
                                ! (used if EPBL_MSTAR_SCHEME = OM4)
NSTAR = 0.06                    !   [nondim] default = 0.2
                                ! The portion of the buoyant potential energy imparted by surface fluxes that is
                                ! available to drive entrainment at the base of mixed layer when that energy is
                                ! positive.
MSTAR_CONV_ADJ = 0.667          !   [nondim] default = 0.0
                                ! Coefficient used for reducing mstar during convection due to reduction of
                                ! stable density gradient.
USE_MLD_ITERATION = True        !   [Boolean] default = True
                                ! A logical that specifies whether or not to use the distance to the bottom of
                                ! the actively turbulent boundary layer to help set the EPBL length scale.
EPBL_TRANSITION_SCALE = 0.01    !   [nondim] default = 0.1
                                ! A scale for the mixing length in the transition layer at the edge of the
                                ! boundary layer as a fraction of the boundary layer thickness.
MLD_ITERATION_GUESS = False     !   [Boolean] default = False
                                ! If true, use the previous timestep MLD as a first guess in the MLD iteration,
                                ! otherwise use half the ocean depth as the first guess of the boundary layer
                                ! depth.  The default is false to facilitate reproducibility.
EPBL_MLD_TOLERANCE = 1.0        !   [meter] default = 1.0
                                ! The tolerance for the iteratively determined mixed layer depth.  This is only
                                ! used with USE_MLD_ITERATION.
EPBL_MLD_BISECTION = False      !   [Boolean] default = False
                                ! If true, use bisection with the iterative determination of the self-consistent
                                ! mixed layer depth.  Otherwise use the false position after a maximum and
                                ! minimum bound have been evaluated and the returned value or bisection before
                                ! this.
EPBL_MLD_MAX_ITS = 20           ! default = 20
                                ! The maximum number of iterations that can be used to find a self-consistent
                                ! mixed layer depth.  If EPBL_MLD_BISECTION is true, the maximum number
                                ! iteractions needed is set by Depth/2^MAX_ITS < EPBL_MLD_TOLERANCE.
EPBL_MIN_MIX_LEN = 0.0          !   [meter] default = 0.0
                                ! The minimum mixing length scale that will be used by ePBL.  The default (0)
                                ! does not set a minimum.
MIX_LEN_EXPONENT = 1.0          !   [nondim] default = 2.0
                                ! The exponent applied to the ratio of the distance to the MLD and the MLD depth
                                ! which determines the shape of the mixing length. This is only used if
                                ! USE_MLD_ITERATION is True.
EPBL_VEL_SCALE_SCHEME = "CUBE_ROOT_TKE" ! default = "CUBE_ROOT_TKE"
                                ! Selects the method for translating TKE into turbulent velocities. Valid values
                                ! are:
                                !    CUBE_ROOT_TKE  - A constant times the cube root of remaining TKE.
                                !    REICHL_H18 - Use the scheme based on a combination of w* and v* as
                                !                 documented in Reichl & Hallberg, 2018.
WSTAR_USTAR_COEF = 1.0          !   [nondim] default = 1.0
                                ! A ratio relating the efficiency with which convectively released energy is
                                ! converted to a turbulent velocity, relative to mechanically forced TKE. Making
                                ! this larger increases the BL diffusivity
EPBL_VEL_SCALE_FACTOR = 1.0     !   [nondim] default = 1.0
                                ! An overall nondimensional scaling factor for wT. Making this larger increases
                                ! the PBL diffusivity.
VSTAR_SURF_FAC = 1.2            !   [nondim] default = 1.2
                                ! The proportionality times ustar to set vstar at the surface.
USE_LA_LI2016 = True            !   [Boolean] default = False
                                ! A logical to use the Li et al. 2016 (submitted) formula to determine the
                                ! Langmuir number.
EPBL_LANGMUIR_SCHEME = "ADDITIVE" ! default = "NONE"
                                ! EPBL_LANGMUIR_SCHEME selects the method for including Langmuir turbulence.
                                ! Valid values are:
                                !    NONE     - Do not do any extra mixing due to Langmuir turbulence
                                !    RESCALE  - Use a multiplicative rescaling of mstar to account for Langmuir
                                !      turbulence
                                !    ADDITIVE - Add a Langmuir turblence contribution to mstar to other
                                !      contributions
LT_ENHANCE_COEF = 0.044         !   [nondim] default = 0.447
                                ! Coefficient for Langmuir enhancement of mstar
LT_ENHANCE_EXP = -1.5           !   [nondim] default = -1.33
                                ! Exponent for Langmuir enhancementt of mstar
LT_MOD_LAC1 = 0.0               !   [nondim] default = -0.87
                                ! Coefficient for modification of Langmuir number due to MLD approaching Ekman
                                ! depth.
LT_MOD_LAC2 = 0.0               !   [nondim] default = 0.0
                                ! Coefficient for modification of Langmuir number due to MLD approaching stable
                                ! Obukhov depth.
LT_MOD_LAC3 = 0.0               !   [nondim] default = 0.0
                                ! Coefficient for modification of Langmuir number due to MLD approaching
                                ! unstable Obukhov depth.
LT_MOD_LAC4 = 0.0               !   [nondim] default = 0.95
                                ! Coefficient for modification of Langmuir number due to ratio of Ekman to
                                ! stable Obukhov depth.
LT_MOD_LAC5 = 0.22              !   [nondim] default = 0.95
                                ! Coefficient for modification of Langmuir number due to ratio of Ekman to
                                ! unstable Obukhov depth.
!EPBL_USTAR_MIN = 1.45842E-18   !   [m s-1]
                                ! The (tiny) minimum friction velocity used within the ePBL code, derived from
                                ! OMEGA and ANGSTROM.

! === module MOM_regularize_layers ===
REGULARIZE_SURFACE_LAYERS = False !   [Boolean] default = False
                                ! If defined, vertically restructure the near-surface layers when they have too
                                ! much lateral variations to allow for sensible lateral barotropic transports.

! === module MOM_opacity ===
EXP_OPACITY_SCHEME = "SINGLE_EXP" ! default = "SINGLE_EXP"
                                ! This character string specifies which exponential opacity scheme to utilize.
                                ! Currently valid options include:
                                !        SINGLE_EXP - Single Exponent decay.
                                !        DOUBLE_EXP - Double Exponent decay.
PEN_SW_SCALE = 15.0             !   [m] default = 0.0
                                ! The vertical absorption e-folding depth of the penetrating shortwave
                                ! radiation.
PEN_SW_FRAC = 0.42              !   [nondim] default = 0.0
                                ! The fraction of the shortwave radiation that penetrates below the surface.
PEN_SW_NBANDS = 1               ! default = 1
                                ! The number of bands of penetrating shortwave radiation.
OPTICS_ANSWER_DATE = 99991231   ! default = 99991231
                                ! The vintage of the order of arithmetic and expressions in the optics
                                ! calculations.  Values below 20190101 recover the answers from the end of 2018,
                                ! while higher values use updated and more robust forms of the same expressions.
PEN_SW_FLUX_ABSORB = 2.5E-11    !   [degC m s-1] default = 2.5E-11
                                ! A minimum remaining shortwave heating rate that will be simply absorbed in the
                                ! next sufficiently thick layers for computational efficiency, instead of
                                ! continuing to penetrate.  The default, 2.5e-11 degC m s-1, is about 1e-4 W m-2
                                ! or 0.08 degC m century-1, but 0 is also a valid value.
PEN_SW_ABSORB_MINTHICK = 1.0    !   [m] default = 1.0
                                ! A thickness that is used to absorb the remaining penetrating shortwave heat
                                ! flux when it drops below PEN_SW_FLUX_ABSORB.
OPACITY_LAND_VALUE = 10.0       !   [m-1] default = 10.0
                                ! The value to use for opacity over land. The default is 10 m-1 - a value for
                                ! muddy water.

! === module MOM_tracer_advect ===
TRACER_ADVECTION_SCHEME = "PPM:H3" ! default = "PLM"
                                ! The horizontal transport scheme for tracers:
                                !   PLM    - Piecewise Linear Method
                                !   PPM:H3 - Piecewise Parabolic Method (Huyhn 3rd order)
                                !   PPM    - Piecewise Parabolic Method (Colella-Woodward)
USE_HUYNH_STENCIL_BUG = False   !   [Boolean] default = False
                                ! If true, use a stencil width of 2 in PPM:H3 tracer advection. This is
                                ! incorrect and will produce regressions in certain configurations, but may be
                                ! required to reproduce results in legacy simulations.

! === module MOM_tracer_hor_diff ===
KHTR = 0.0                      !   [m2 s-1] default = 0.0
                                ! The background along-isopycnal tracer diffusivity.
KHTR_MIN = 0.0                  !   [m2 s-1] default = 0.0
                                ! The minimum along-isopycnal tracer diffusivity.
KHTR_MAX = 0.0                  !   [m2 s-1] default = 0.0
                                ! The maximum along-isopycnal tracer diffusivity.
KHTR_PASSIVITY_COEFF = 0.0      !   [nondim] default = 0.0
                                ! The coefficient that scales deformation radius over grid-spacing in passivity,
                                ! where passivity is the ratio between along isopycnal mixing of tracers to
                                ! thickness mixing. A non-zero value enables this parameterization.
KHTR_PASSIVITY_MIN = 0.5        !   [nondim] default = 0.5
                                ! The minimum passivity which is the ratio between along isopycnal mixing of
                                ! tracers to thickness mixing.
DIFFUSE_ML_TO_INTERIOR = False  !   [Boolean] default = False
                                ! If true, enable epipycnal mixing between the surface boundary layer and the
                                ! interior.
CHECK_DIFFUSIVE_CFL = True      !   [Boolean] default = False
                                ! If true, use enough iterations the diffusion to ensure that the diffusive
                                ! equivalent of the CFL limit is not violated.  If false, always use the greater
                                ! of 1 or MAX_TR_DIFFUSION_CFL iteration.
MAX_TR_DIFFUSION_CFL = -1.0     !   [nondim] default = -1.0
                                ! If positive, locally limit the along-isopycnal tracer diffusivity to keep the
                                ! diffusive CFL locally at or below this value.  The number of diffusive
                                ! iterations is often this value or the next greater integer.
RECALC_NEUTRAL_SURF = False     !   [Boolean] default = False
                                ! If true, then recalculate the neutral surfaces if the
                                ! diffusive CFL is exceeded. If false, assume that the
                                ! positions of the surfaces do not change

! === module MOM_neutral_diffusion ===
! This module implements neutral diffusion of tracers
USE_NEUTRAL_DIFFUSION = False   !   [Boolean] default = False
                                ! If true, enables the neutral diffusion module.

! === module MOM_hor_bnd_diffusion ===
! This module implements horizontal diffusion of tracers near boundaries
USE_HORIZONTAL_BOUNDARY_DIFFUSION = False !   [Boolean] default = False
                                ! If true, enables the horizonal boundary tracer's diffusion module.
OBSOLETE_DIAGNOSTIC_IS_FATAL = True !   [Boolean] default = True
                                ! If an obsolete diagnostic variable appears in the diag_table, cause a FATAL
                                ! error rather than issue a WARNING.

! === module MOM_sum_output ===
CALCULATE_APE = True            !   [Boolean] default = True
                                ! If true, calculate the available potential energy of the interfaces.  Setting
                                ! this to false reduces the memory footprint of high-PE-count models
                                ! dramatically.
WRITE_STOCKS = True             !   [Boolean] default = True
                                ! If true, write the integrated tracer amounts to stdout when the energy files
                                ! are written.
MAXTRUNC = 10000                !   [truncations save_interval-1] default = 0
                                ! The run will be stopped, and the day set to a very large value if the velocity
                                ! is truncated more than MAXTRUNC times between energy saves.  Set MAXTRUNC to 0
                                ! to stop if there is any truncation of velocities.
MAX_ENERGY = 0.0                !   [m2 s-2] default = 0.0
                                ! The maximum permitted average energy per unit mass; the model will be stopped
                                ! if there is more energy than this.  If zero or negative, this is set to
                                ! 10*MAXVEL^2.
ENERGYFILE = "ocean.stats"      ! default = "ocean.stats"
                                ! The file to use to write the energies and globally summed diagnostics.
DATE_STAMPED_STDOUT = True      !   [Boolean] default = True
                                ! If true, use dates (not times) in messages to stdout
TIMEUNIT = 8.64E+04             !   [s] default = 8.64E+04
                                ! The time unit in seconds a number of input fields
READ_DEPTH_LIST = False         !   [Boolean] default = False
                                ! Read the depth list from a file if it exists or create that file otherwise.
DEPTH_LIST_MIN_INC = 1.0E-10    !   [m] default = 1.0E-10
                                ! The minimum increment between the depths of the entries in the depth-list
                                ! file.
ENERGYSAVEDAYS = 1.0            !   [days] default = 1.0
                                ! The interval in units of TIMEUNIT between saves of the energies of the run and
                                ! other globally summed diagnostics.
ENERGYSAVEDAYS_GEOMETRIC = 0.0  !   [days] default = 0.0
                                ! The starting interval in units of TIMEUNIT for the first call to save the
                                ! energies of the run and other globally summed diagnostics. The interval
                                ! increases by a factor of 2. after each call to write_energy.

! === module ocean_stochastics_init ===
DO_SPPT = False                 !   [Boolean] default = False
                                ! If true, then stochastically perturb the thermodynamic tendemcies of T,S, amd
                                ! h.  Amplitude and correlations are controlled by the nam_stoch namelist in the
                                ! UFS model only.
PERT_EPBL = False               !   [Boolean] default = False
                                ! If true, then stochastically perturb the kinetic energy production and
                                ! dissipation terms.  Amplitude and correlations are controlled by the nam_stoch
                                ! namelist in the UFS model only.

! === module ocean_model_init ===
SINGLE_STEPPING_CALL = True     !   [Boolean] default = True
                                ! If true, advance the state of MOM with a single step including both dynamics
                                ! and thermodynamics.  If false, the two phases are advanced with separate
                                ! calls.
RESTART_CONTROL = 1             ! default = 1
                                ! An integer whose bits encode which restart files are written. Add 2 (bit 1)
                                ! for a time-stamped file, and odd (bit 0) for a non-time-stamped file.  A
                                ! restart file will be saved at the end of the run segment for any non-negative
                                ! value.
OCEAN_SURFACE_STAGGER = "A"     ! default = "C"
                                ! A case-insensitive character string to indicate the staggering of the surface
                                ! velocity field that is returned to the coupler.  Valid values include 'A',
                                ! 'B', or 'C'.
EPS_OMESH = 1.0E-13             !   [degrees] default = 1.0E-04
                                ! Maximum allowable difference between ESMF mesh and MOM6 domain coordinates in
                                ! nuopc cap.
RESTORE_SALINITY = True         !   [Boolean] default = False
                                ! If true, the coupled driver will add a globally-balanced fresh-water flux that
                                ! drives sea-surface salinity toward specified values.
RESTORE_TEMPERATURE = False     !   [Boolean] default = False
                                ! If true, the coupled driver will add a heat flux that drives sea-surface
                                ! temperature toward specified values.
ICE_SHELF = False               !   [Boolean] default = False
                                ! If true, enables the ice shelf model.
ICEBERGS_APPLY_RIGID_BOUNDARY = False !   [Boolean] default = False
                                ! If true, allows icebergs to change boundary condition felt by ocean
USE_WAVES = False               !   [Boolean] default = False
                                ! If true, enables surface wave modules.

! === module MOM_surface_forcing_nuopc ===
LATENT_HEAT_FUSION = 3.337E+05  !   [J/kg] default = 3.34E+05
                                ! The latent heat of fusion.
LATENT_HEAT_VAPORIZATION = 2.501E+06 !   [J/kg] default = 2.5E+06
                                ! The latent heat of fusion.
MAX_P_SURF = 0.0                !   [Pa] default = -1.0
                                ! The maximum surface pressure that can be exerted by the atmosphere and
                                ! floating sea-ice or ice shelves. This is needed because the FMS coupling
                                ! structure does not limit the water that can be frozen out of the ocean and the
                                ! ice-ocean heat fluxes are treated explicitly.  No limit is applied if a
                                ! negative value is used.
ADJUST_NET_SRESTORE_TO_ZERO = True !   [Boolean] default = True
                                ! If true, adjusts the salinity restoring seen to zero whether restoring is via
                                ! a salt flux or virtual precip.
ADJUST_NET_SRESTORE_BY_SCALING = False !   [Boolean] default = False
                                ! If true, adjustments to salt restoring to achieve zero net are made by scaling
                                ! values without moving the zero contour.
ADJUST_NET_FRESH_WATER_TO_ZERO = True !   [Boolean] default = False
                                ! If true, adjusts the net fresh-water forcing seen by the ocean (including
                                ! restoring) to zero.
USE_NET_FW_ADJUSTMENT_SIGN_BUG = False !   [Boolean] default = False
                                ! If true, use the wrong sign for the adjustment to the net fresh-water.
ADJUST_NET_FRESH_WATER_BY_SCALING = False !   [Boolean] default = False
                                ! If true, adjustments to net fresh water to achieve zero net are made by
                                ! scaling values without moving the zero contour.
ICE_SALT_CONCENTRATION = 0.005  !   [kg/kg] default = 0.005
                                ! The assumed sea-ice salinity needed to reverse engineer the melt flux (or
                                ! ice-ocean fresh-water flux).
USE_LIMITED_PATM_SSH = True     !   [Boolean] default = True
                                ! If true, return the sea surface height with the correction for the atmospheric
                                ! (and sea-ice) pressure limited by max_p_surf instead of the full atmospheric
                                ! pressure.
WIND_STAGGER = "A"              ! default = "C"
                                ! A case-insensitive character string to indicate the staggering of the input
                                ! wind stress field.  Valid values are 'A', 'B', or 'C'.
WIND_STRESS_MULTIPLIER = 1.0    !   [nondim] default = 1.0
                                ! A factor multiplying the wind-stress given to the ocean by the coupler. This
                                ! is used for testing and should be =1.0 for any production runs.
ENTHALPY_FROM_COUPLER = True    !   [Boolean] default = False
                                ! If True, the heat (enthalpy) associated with mass entering/leaving the ocean
                                ! is provided via coupler.
FLUXCONST = 0.11                !   [m day-1] default = 0.0
                                ! The constant that relates the restoring surface fluxes to the relative surface
                                ! anomalies (akin to a piston velocity).  Note the non-MKS units.
SALT_RESTORE_FILE = "salt_sfc_restore.nc" ! default = "salt_restore.nc"
                                ! A file in which to find the surface salinity to use for restoring.
SALT_RESTORE_VARIABLE = "salt"  ! default = "salt"
                                ! The name of the surface salinity variable to read from SALT_RESTORE_FILE for
                                ! restoring salinity.
SRESTORE_AS_SFLUX = True        !   [Boolean] default = False
                                ! If true, the restoring of salinity is applied as a salt flux instead of as a
                                ! freshwater flux.
MAX_DELTA_SRESTORE = 999.0      !   [PSU or g kg-1] default = 999.0
                                ! The maximum salinity difference used in restoring terms.
MASK_SRESTORE_UNDER_ICE = False !   [Boolean] default = False
                                ! If true, disables SSS restoring under sea-ice based on a frazil criteria
                                ! (SST<=Tf). Only used when RESTORE_SALINITY is True.
MASK_SRESTORE_MARGINAL_SEAS = False !   [Boolean] default = False
                                ! If true, disable SSS restoring in marginal seas. Only used when
                                ! RESTORE_SALINITY is True.
BASIN_FILE = "basin.nc"         ! default = "basin.nc"
                                ! A file in which to find the basin masks, in variable 'basin'.
MASK_SRESTORE = False           !   [Boolean] default = False
                                ! If true, read a file (salt_restore_mask) containing a mask for SSS restoring.
CD_TIDES = 1.0E-04              !   [nondim] default = 1.0E-04
                                ! The drag coefficient that applies to the tides.
READ_GUST_2D = False            !   [Boolean] default = False
                                ! If true, use a 2-dimensional gustiness supplied from an input file
GUST_CONST = 0.0                !   [Pa] default = 0.0
                                ! The background gustiness in the winds.
USTAR_GUSTLESS_BUG = False      !   [Boolean] default = False
                                ! If true include a bug in the time-averaging of the gustless wind friction
                                ! velocity
USE_RIGID_SEA_ICE = True        !   [Boolean] default = False
                                ! If true, sea-ice is rigid enough to exert a nonhydrostatic pressure that
                                ! resist vertical motion.
SEA_ICE_MEAN_DENSITY = 900.0    !   [kg m-3] default = 900.0
                                ! A typical density of sea ice, used with the kinematic viscosity, when
                                ! USE_RIGID_SEA_ICE is true.
SEA_ICE_VISCOSITY = 1.0E+09     !   [m2 s-1] default = 1.0E+09
                                ! The kinematic viscosity of sufficiently thick sea ice for use in calculating
                                ! the rigidity of sea ice.
SEA_ICE_RIGID_MASS = 100.0      !   [kg m-2] default = 1000.0
                                ! The mass of sea-ice per unit area at which the sea-ice starts to exhibit
                                ! rigidity
ALLOW_ICEBERG_FLUX_DIAGNOSTICS = False !   [Boolean] default = False
                                ! If true, makes available diagnostics of fluxes from icebergs as seen by MOM6.
ALLOW_FLUX_ADJUSTMENTS = False  !   [Boolean] default = False
                                ! If true, allows flux adjustments to specified via the data_table using the
                                ! component name 'OCN'.
LIQUID_RUNOFF_FROM_DATA = False !   [Boolean] default = False
                                ! If true, allows liquid river runoff to be specified via the data_table using
                                ! the component name 'OCN'.

! === module MOM_restart ===
WAVE_INTERFACE_ANSWER_DATE = 20221231 ! default = 20221231
                                ! The vintage of the order of arithmetic and expressions in the surface wave
                                ! calculations.  Values below 20230101 recover the answers from the end of 2022,
                                ! while higher values use updated and more robust forms of the same expressions:
                                !    <  20230101 - Original answers for wave interface routines
                                !    >= 20230101 - More robust expressions for Update_Stokes_Drift
                                !    >= 20230102 - More robust expressions for get_StokesSL_LiFoxKemper
                                !    >= 20230103 - More robust expressions for ust_2_u10_coare3p5
LA_DEPTH_RATIO = 0.04           !   [nondim] default = 0.04
                                ! The depth (normalized by BLD) to average Stokes drift over in Langmuir number
                                ! calculation, where La = sqrt(ust/Stokes).
LA_DEPTH_MIN = 0.1              !   [m] default = 0.1
                                ! The minimum depth over which to average the Stokes drift in the Langmuir
                                ! number calculation.
VISCOSITY_AIR = 1.0E-06         !   [m2 s-1] default = 1.0E-06
                                ! A typical viscosity of air at sea level, as used in wave calculations
VON_KARMAN_WAVES = 0.4          !   [nondim] default = 0.4
                                ! The value the von Karman constant as used for surface wave calculations.
RHO_AIR = 1.225                 !   [kg m-3] default = 1.225
                                ! A typical density of air at sea level, as used in wave calculations
RHO_SFC_WAVES = 1035.0          !   [kg m-3] default = 1035.0
                                ! A typical surface density of seawater, as used in wave calculations in
                                ! comparison with the density of air.  The default is RHO_0.
WAVE_HEIGHT_SCALE_FACTOR = 0.0246 !   [s2 m-1] default = 0.0246
                                ! A factor relating the square of the 10 m wind speed to the significant wave
                                ! height, with a default value based on the Pierson-Moskowitz spectrum.
CHARNOCK_MIN = 0.028            !   [nondim] default = 0.028
                                ! The minimum value of the Charnock coefficient, which relates the square of the
                                ! air friction velocity divided by the gravitational acceleration to the wave
                                ! roughness length.
CHARNOCK_SLOPE_U10 = 0.0017     !   [s m-1] default = 0.0017
                                ! The partial derivative of the Charnock coefficient with the 10 m wind speed.
                                ! Note that in eq. 13 of the Edson et al. 2013 describing the COARE 3.5 bulk
                                ! flux algorithm, this slope is given as 0.017.  However, 0.0017 reproduces the
                                ! curve in their figure 6, so that is the default value used in MOM6.
CHARNOCK_0_WIND_INTERCEPT = -0.005 !   [nondim] default = -0.005
                                ! The intercept of the fit for the Charnock coefficient in the limit of no wind.
                                ! Note that this can be negative because CHARNOCK_MIN will keep the final value
                                ! for the Charnock coefficient from being from being negative.

! === module MOM_file_parser ===
SEND_LOG_TO_STDOUT = False      !   [Boolean] default = False
                                ! If true, all log messages are also sent to stdout.
DOCUMENT_FILE = "MOM_parameter_doc" ! default = "MOM_parameter_doc"
                                ! The basename for files where run-time parameters, their settings, units and
                                ! defaults are documented. Blank will disable all parameter documentation.
COMPLETE_DOCUMENTATION = True   !   [Boolean] default = True
                                ! If true, all run-time parameters are documented in MOM_parameter_doc.all .
MINIMAL_DOCUMENTATION = True    !   [Boolean] default = True
                                ! If true, non-default run-time parameters are documented in
                                ! MOM_parameter_doc.short .

