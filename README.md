# Cloudy Incentives for Solar: How Distortions in Retail Electricity Pricing Affect the Value of Distributed Generation
Exploring the distortionary impact of California's net energy metering (NEM) policies on distributed energy resource (DER) investment decisions for SPI 582B: The Economics of Climate Change Policy.

# TODO
1. Use PySAM's PVWatts module to generate 8760s for each representative generation profile (by region, mounting and tracking method, azimuth and tilt).
2. Use PySAM's UtilityRate module to calculate revenue from each representative generation profile under NEM 1.0 and 2.0 (based on utility service territories).
3. Redo logic of assigning sites to a normalized generation profile before scaling by system capacity. 
5. Download 5-minute real-time LMPs for sub-LAPs in CAISO and take hourly average to compare against 8760 generation profiles.
6. Redo logic of assigning sites to a grid node and associated LMPs. 
7. Compare switch from NEM 1.0 and 2.0 to California's new policy, NEM 3.0 (which is actually net billing). 
8. Incorporate distribution losses (see MIT's Utility of the Future)?
