TRAIN_DATA = [
    ("Buy Crude from ADM BULGARIA", 
    {"entities": [(0, 3, "contractTypeDisplayName"), (4, 9, "productIdDisplayName"), (15, 27, "cpNameDisplayName")]}),
    
    ("Sold gasoil to ADM BULGARIA.", 
    {"entities": [(0, 4, "contractTypeDisplayName"), (5, 11, "productIdDisplayName"), (15, 27, "cpNameDisplayName")]}),
    
    ("Bought gasoil from 23-7 Farms.", 
    {"entities": [(0, 6, "contractTypeDisplayName"), (7, 13, "productIdDisplayName"), (19, 29, "cpNameDisplayName")]}),
    
    ("Buy 10 MT Crude from Supplier-1, ex CIF, in USD.", 
    {"entities": [(0, 3, "contractTypeDisplayName"), (4, 6, "itemQty"),(7,9,"itemQtyUnitIdDisplayName"), (10, 15, "productIdDisplayName"), (21, 31, "cpNameDisplayName"), (36, 39,"incotermIdDisplayName"), (44, 47,"payInCurIdDisplayName")]}),
    
    ("Sell gasoil to A&M Global Transport Inc.", 
    {"entities": [(0, 4, "contractTypeDisplayName"), (5, 11, "productIdDisplayName"), (17, 41, "cpNameDisplayName")]}),
    
    ("Bought Crude from A&M Global Transport Inc.", 
    {"entities": [(0, 6, "contractTypeDisplayName"), (7, 13, "productIdDisplayName"), (19, 43, "cpNameDisplayName")]}),
    
    ("Purchase Crude from 23-7 Farms.", 
    {"entities": [(0, 8, "contractTypeDisplayName"), (9, 14, "productIdDisplayName"), (20, 30, "cpNameDisplayName")]}),
    
    ("From 23-7 Farms Purchase Crude.", 
    {"entities": [(5, 15, "cpNameDisplayName"), (16, 24, "contractTypeDisplayName"), (25, 30, "productIdDisplayName")]}),
    
    ("Purchase Crude.", 
    {"entities": [(0, 8, "contractTypeDisplayName"), (9, 14, "productIdDisplayName")]}),

    ("Sell Gasoil.", 
    {"entities": [(0, 4, "contractTypeDisplayName"), (5, 11, "productIdDisplayName")]}),

    ("Buy Gasoil of 10 PPM and 2000 MT.", 
    {"entities": [(0, 3, "contractTypeDisplayName"), (4, 10, "productIdDisplayName"), (14, 20, "qualityDisplayName"), (25, 29, "itemQty"), (30, 32, "itemQtyUnitIdDisplayName")]}),  

    ("Buy 2000 MT Gasoil of qualityDisplayName 1 PPM.", 
    {"entities": [(0, 3, "contractTypeDisplayName"), (4, 8, "itemQty"), (9, 11, "itemQtyUnitIdDisplayName"), (12, 18, "productIdDisplayName"), (30, 35, "qualityDisplayName")]}),  

    ("Buy 2000 MT Gasoil of qualityDisplayName 100 PPM.", 
    {"entities": [(0, 3, "contractTypeDisplayName"), (4, 8, "itemQty"), (9, 11, "itemQtyUnitIdDisplayName"), (12, 18, "productIdDisplayName"), (30, 37, "qualityDisplayName")]}),  

    ("Purchase gasoil of qualityDisplayName 10 PPM of Quantity 2000 MT Through DAP.", 
    {"entities": [(0, 8, "contractTypeDisplayName"), (9, 15, "productIdDisplayName"), (27, 33, "qualityDisplayName"), (46, 50, "itemQty"), (51, 53, "itemQtyUnitIdDisplayName"), (62, 65, "incotermIdDisplayName")]}),

    ("Sell 100 MT gasoil of qualityDisplayName 10 PPM through DAP.",
    {"entities": [(0, 4, "contractTypeDisplayName"), (5, 8, "itemQty"), (9, 11, "itemQtyUnitIdDisplayName"), (12, 18, "productIdDisplayName"), (30, 36, "qualityDisplayName"), (45, 48, "incotermIdDisplayName")]}),

    ("Sold 1000 MT 10 PPM gasoil through DAP.",
    {"entities": [(0, 4, "contractTypeDisplayName"), (5, 9, "itemQty"), (10, 12, "itemQtyUnitIdDisplayName"), (13, 19, "qualityDisplayName"), (20, 26, "productIdDisplayName"), (35, 38, "incotermIdDisplayName")]}),
    
    ("Sold 1000 MT, 100 PPM gasoil through CIF.",
    {"entities": [(0, 4, "contractTypeDisplayName"), (5, 9, "itemQty"), (10, 12, "itemQtyUnitIdDisplayName"), (14, 21, "qualityDisplayName"), (22, 28, "productIdDisplayName"), (37, 40, "incotermIdDisplayName")]}),

    ("Bought gasoil of qualityDisplayName 1000 PPM of Quantity 2000 MT through CIF.", 
    {"entities": [(0, 6, "contractTypeDisplayName"), (7, 13, "productIdDisplayName"), (25, 33, "qualityDisplayName"), (46, 50, "itemQty"), (51, 53, "itemQtyUnitIdDisplayName"), (62, 65, "incotermIdDisplayName")]}),
 
    ("Buy 1000 MT, 10 PPM gasoil through DAP.",
    {"entities": [(0, 3, "contractTypeDisplayName"), (4, 8, "itemQty"), (9, 11, "itemQtyUnitIdDisplayName"), (13, 19, "qualityDisplayName"), (20, 26, "productIdDisplayName"), (35, 38, "incotermIdDisplayName")]}),

    ("Sell 10 ppm gasoil, 1000 MT, on CIF terms.",
    {"entities": [(0, 4, "contractTypeDisplayName"), (5, 11, "qualityDisplayName"), (12, 18, "productIdDisplayName"), (20, 24, "itemQty"), (25, 27, "itemQtyUnitIdDisplayName"), (32, 35, "incotermIdDisplayName")]}),

    ("Sold 1000 MT, 10 ppm type gasoil, on CIF terms, in USD",
    {"entities": [(0, 4, "contractTypeDisplayName"), (5, 9, "itemQty"), (10, 12, "itemQtyUnitIdDisplayName"), (14, 20, "qualityDisplayName"), (26, 32, "productIdDisplayName"), (37, 40, "incotermIdDisplayName"), (51, 54, "payInCurIdDisplayName")]}),

    ("Sell 1000 MT cotton, on CIF terms, in USD.",
    {"entities": [(0, 4, "contractTypeDisplayName"), (5, 9, "itemQty"), (10, 12, "itemQtyUnitIdDisplayName"), (13, 19, "productIdDisplayName"), (24, 27, "incotermIdDisplayName"), (38, 41, "payInCurIdDisplayName")]}),
    
    ("Sell 1000 MT cotton, on CIF terms, in USD.",
    {"entities": [(0, 4, "contractTypeDisplayName"), (5, 9, "itemQty"), (10, 12, "itemQtyUnitIdDisplayName"), (13, 19, "productIdDisplayName"), (24, 27, "incotermIdDisplayName"), (38, 41, "payInCurIdDisplayName")]}),

    ("Sale Brent of 38 API ,ex -FOB North sea to cpNameDisplayName ADC Warehousing.",
    {"entities": [(0, 4, "contractTypeDisplayName"), (5, 10, "product-qualityDisplayName"), (14, 20, "qualityDisplayName"), (26, 29, "incotermIdDisplayName"), (30, 39, "originationCountryIdDisplayName"), (56, 71, "cpNameDisplayName")]}),

    ("Sale Fuel oil ex-FOB Singapore for loading from Port of Singapore.",
    {"entities": [(0, 4, "contractTypeDisplayName"), (5, 13, "productIdDisplayName"), (17, 20, "incotermIdDisplayName"), (21, 30, "originationCountryIdDisplayName"), (48, 52, "loadingLocationGroupTypeIdDisplayName"), (56, 65, "originationCityIdDisplayName")]}),

    ("Buy gas oil 5000 MT of 500ppm sulphur ex -CIF from cpNameDisplayName B for discharge in Dubai at port of Hormuz",
    {"entities": [(0, 3, "contractTypeDisplayName"), (4, 11, "productIdDisplayName"), (12, 16, "itemQty"), (17, 19, "itemQtyUnitIdDisplayName"), (23, 37, "qualityDisplayName"), (42, 45, "incotermIdDisplayName"), (64,65,"cpNameDisplayName"), (83,88,"destinationCountryIdDisplayName"), (92, 96, "destinationLocationGroupTypeId"), (100, 106, "destinationCityIdDisplayName")]}),

    ("Bought 5000 MT gas oil of 10 ppm sulphur ex CIF from Aramco loading from port of Hormuz, Dubai and discharging to port of Hormuz, Dubai",
    {"entities": [(0, 6, "contractTypeDisplayName"), (7, 11, "itemQty"), (12, 14, "itemQtyUnitIdDisplayName"), (15, 22, "productIdDisplayName"), (26, 40, "qualityDisplayName"), (44, 47, "incotermIdDisplayName"), (53,59,"cpNameDisplayName"), (73,77,"loadingLocationGroupTypeIdDisplayName"), (81, 87, "originationCityIdDisplayName"), (89,94,"originationCountryIdDisplayName"), (114, 118, "destinationLocationGroupTypeId"), (122, 128, "destinationCityIdDisplayName"), (130, 135,"destinationCountryIdDisplayName")]}),

    ("Bought 5000 MT gas oil of 10 ppm sulphur ex CIF from Aramco loading from port of Hormuz, Dubai and discharging to port of Hormuz, Dubai",
    {"entities": [(0, 6, "contractTypeDisplayName"), (7, 11, "itemQty"), (12, 14, "itemQtyUnitIdDisplayName"), (15, 22, "productIdDisplayName"), (26, 40, "qualityDisplayName"), (44, 47, "incotermIdDisplayName"), (53,59,"cpNameDisplayName"), (73,77,"loadingLocationGroupTypeIdDisplayName"), (81, 87, "originationCityIdDisplayName"), (89,94,"originationCountryIdDisplayName"), (114, 118, "destinationLocationGroupTypeId"), (122, 128, "destinationCityIdDisplayName"), (130, 135,"destinationCountryIdDisplayName")]}),

    ("Bought 5000 MT gas oil of 10 ppm sulphur ex CIF from Aramco loading from Brisbane, Australia and discharging to Durres, Albania",
    {"entities": [(0, 6, "contractTypeDisplayName"), (7, 11, "itemQty"), (12, 14, "itemQtyUnitIdDisplayName"), (15, 22, "productIdDisplayName"), (26, 40, "qualityDisplayName"), (44, 47, "incotermIdDisplayName"), (53,59,"cpNameDisplayName"), (73,81,"originationCityIdDisplayName"), (83, 87, "originationCountryIdDisplayName"), (107,113,"destinationCityIdDisplayName"), (115, 122, "destinationCountryIdDisplayName")]}),

    ("Bought 5000 MT gas oil of 10 ppm sulphur ex DAP from Aramco loading from Brisbane, Australia and discharging to Durres, Albania",
    {"entities": [(0, 6, "contractTypeDisplayName"), (7, 11, "itemQty"), (12, 14, "itemQtyUnitIdDisplayName"), (15, 22, "productIdDisplayName"), (26, 40, "qualityDisplayName"), (44, 47, "incotermIdDisplayName"), (53,59,"cpNameDisplayName"), (73,81,"originationCityIdDisplayName"), (83, 87, "originationCountryIdDisplayName"), (107,113,"destinationCityIdDisplayName"), (115, 122, "destinationCountryIdDisplayName")]}),

    ("Sold 100 M3 gasoil, Gasoil 10ppm, ex FOB, in USD, to ADM BULGARIA loading from Brisbane, Australia and discharging to Buenos Aires, Argentina",
    {"entities": [(0, 4, "contractTypeDisplayName"), (5, 8, "itemQty"), (9, 11, "itemQtyUnitIdDisplayName"), (12, 18, "productIdDisplayName"), (20, 32, "qualityDisplayName"), (37, 40, "incotermIdDisplayName"), (45, 48, "payInCurIdDisplayName"), (53,65,"cpNameDisplayName"), (79,87,"originationCityIdDisplayName"), (89, 98, "originationCountryIdDisplayName"), (118, 130,"destinationCityIdDisplayName"), (132, 141, "destinationCountryIdDisplayName")]}),

    ("Sold 100 M3 gasoil, Gasoil 10ppm, ex FOB, in USD, to ADM BULGARIA loading from Brisbane, Australia and discharging to Buenos Aires, Argentina",
    {"entities": [(0, 4, "contractTypeDisplayName"), (5, 8, "itemQty"), (9, 11, "itemQtyUnitIdDisplayName"), (12, 18, "productIdDisplayName"), (20, 32, "qualityDisplayName"), (37, 40, "incotermIdDisplayName"), (45, 48, "payInCurIdDisplayName"), (53,65,"cpNameDisplayName"), (79,87,"originationCityIdDisplayName"), (89, 98, "originationCountryIdDisplayName"), (118, 130,"destinationCityIdDisplayName"), (132, 141, "destinationCountryIdDisplayName")]}),

    ("Sell 100 M3 gasoil, Gasoil 10ppm, ex FOB, in USD, to ADM BULGARIA loading from Brisbane, Australia and discharging to port of Buenos Aires, Argentina",
    {"entities": [(0, 4, "contractTypeDisplayName"), (5, 8, "itemQty"), (9, 11, "itemQtyUnitIdDisplayName"), (12, 18, "productIdDisplayName"), (20, 32, "qualityDisplayName"), (37, 40, "incotermIdDisplayName"), (45, 48, "payInCurIdDisplayName"), (53,65,"cpNameDisplayName"), (79,87,"originationCityIdDisplayName"), (89, 98, "originationCountryIdDisplayName"), (118, 122, "loadingLocationGroupTypeIdDisplayName"), (126,138,"destinationCityIdDisplayName"), (140, 149, "destinationCountryIdDisplayName")]}),

    ("Sold 100 M3 gasoil, 10ppm, ex DAP, in INR, to ADM BULGARIA loading from Brisbane, Australia and discharging to port of Buenos Aires, Argentina",
    {"entities": [(0, 4, "contractTypeDisplayName"), (5, 8, "itemQty"), (9, 11, "itemQtyUnitIdDisplayName"), (12, 18, "productIdDisplayName"), (20, 25, "qualityDisplayName"), (30, 33, "incotermIdDisplayName"), (38, 41, "payInCurIdDisplayName"), (46, 58,"cpNameDisplayName"), (72,80,"originationCityIdDisplayName"), (82, 91, "originationCountryIdDisplayName"), (111, 115, "loadingLocationGroupTypeIdDisplayName"), (119,131,"destinationCityIdDisplayName"), (133, 142, "destinationCountryIdDisplayName")]}),

    ("Sell 10ppm, 2 MT crude to A&M Global Transport Inc., in USD, through DAP, from port of Luanda, Angola to Chennai, India",
    {"entities": [(0, 4, "contractTypeDisplayName"), (5, 10, "qualityDisplayName"), (12, 13, "itemQty"), (14, 16, "itemQtyUnitIdDisplayName"), (17, 22, "productIdDisplayName"), (26, 51, "cpNameDisplayName"), (56, 59, "payInCurIdDisplayName"), (69, 72,"incotermIdDisplayName"), (79,83,"loadingLocationGroupTypeIdDisplayName"), (87, 93, "originationCityIdDisplayName"), (95, 101, "originationCountryIdDisplayName"), (105,112,"destinationCityIdDisplayName"), (114, 119, "destinationCountryIdDisplayName")]}),

    ("Sold 100 ppm, 2 MT gasoil to A&M Global Transport Inc., in USD, on CIF terms, to be delivered from Adelaide, Australia to Durres, Albania",
    {"entities": [(0, 4, "contractTypeDisplayName"), (5, 12, "qualityDisplayName"), (14, 15, "itemQty"), (16, 18, "itemQtyUnitIdDisplayName"), (19, 25, "productIdDisplayName"), (29, 54, "cpNameDisplayName"), (59, 62, "payInCurIdDisplayName"), (67, 70,"incotermIdDisplayName"), (99,107,"originationCityIdDisplayName"), (109, 118, "originationCountryIdDisplayName"), (122, 128, "destinationCityIdDisplayName"), (130,137,"destinationCountryIdDisplayName")]})
    

]