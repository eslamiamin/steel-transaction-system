-- Select POC first, then PROD explicitly in SSMS.
SET XACT_ABORT ON;
BEGIN TRY
BEGIN TRAN;
IF DB_NAME() NOT IN ('SteelTransaction_POC','SteelTransaction_PROD') THROW 50001,'Wrong database',1;
IF OBJECT_ID('dbo.ProductCategories','U') IS NULL CREATE TABLE dbo.ProductCategories(CategoryID int IDENTITY PRIMARY KEY, CategoryName nvarchar(100) NOT NULL UNIQUE);
IF OBJECT_ID('dbo.ProductSubcategories','U') IS NULL CREATE TABLE dbo.ProductSubcategories(SubcategoryID int IDENTITY PRIMARY KEY, CategoryID int NOT NULL REFERENCES dbo.ProductCategories, SubcategoryName nvarchar(100) NOT NULL, UNIQUE(CategoryID,SubcategoryName));
IF COL_LENGTH('dbo.Products','SubcategoryID') IS NULL ALTER TABLE dbo.Products ADD SubcategoryID int NULL REFERENCES dbo.ProductSubcategories;
IF COL_LENGTH('dbo.Products','SizeName') IS NULL ALTER TABLE dbo.Products ADD SizeName nvarchar(100) NULL;
DECLARE @t sysname, @sql nvarchar(max);
DECLARE cur CURSOR LOCAL FAST_FORWARD FOR SELECT name FROM sys.tables WHERE schema_id=SCHEMA_ID('dbo') AND name IN ('PurchasesV4','SalesV4');
OPEN cur; FETCH NEXT FROM cur INTO @t;
WHILE @@FETCH_STATUS=0 BEGIN
IF COL_LENGTH('dbo.'+@t,'ManualInvoiceNo') IS NULL EXEC('ALTER TABLE dbo.'+@t+' ADD ManualInvoiceNo nvarchar(50) NULL');
IF COL_LENGTH('dbo.'+@t,'Notes') IS NULL EXEC('ALTER TABLE dbo.'+@t+' ADD Notes nvarchar(2000) NULL');
IF COL_LENGTH('dbo.'+@t,'Quantity2') IS NULL EXEC('ALTER TABLE dbo.'+@t+' ADD Quantity2 decimal(18,3) NULL, Rate2 decimal(18,2) NULL, CONSTRAINT CK_'+@t+'_Dual CHECK ((Quantity2 IS NULL AND Rate2 IS NULL) OR (Quantity2 IS NOT NULL AND Rate2 IS NOT NULL AND Quantity2>0 AND Rate2>=0))');
IF COL_LENGTH('dbo.'+@t,'TotalQuantity') IS NULL EXEC('ALTER TABLE dbo.'+@t+' ADD TotalQuantity AS (Quantity+ISNULL(Quantity2,0)), TotalAmount AS (Quantity*Rate+ISNULL(Quantity2*Rate2,0))');
FETCH NEXT FROM cur INTO @t; END;
CLOSE cur; DEALLOCATE cur;
COMMIT;
END TRY BEGIN CATCH IF @@TRANCOUNT>0 ROLLBACK; THROW; END CATCH;
