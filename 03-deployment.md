# 03 — Deployment and SQL runbook

## Environment and prerequisites

Windows workstation hosts the application on TCP 8501; SQL Server is a separate central instance. Other LAN clients use the host's LAN IP in a browser. Restrict firewall access to authorized LAN clients. The SQL connection runs under the host process's Windows identity, not each browser user's identity. Original server, workstation path and IP are intentionally redacted.

## Historical setup sequence

1. Create project directory and Python 3.12 virtual environment; install dependencies and ODBC Driver 17.
2. Test Windows-authenticated SQL connection; create SteelTransaction_POC and initial master/purchase tables.
3. Run V2/V3 setup as appropriate, then V4 setup on the existing POC schema. V4 setup depends on original Products, Suppliers and PurchaseTypes tables; a fresh bootstrap is not included in the historical V4 archive.
4. Test local and LAN access. Stop previous Streamlit process before launching a new release on the same port. Old `pages/` files caused duplicate navigation in earlier releases; archive them outside the active app directory.
5. Inventory schema, dependencies and identity columns before copying POC.
6. Back up POC and restore as PROD with separate data/log paths.
7. Clean test transactions in PROD only, then seed production masters. Apply migration to both environments independently. Actual reported state: PROD migrated; POC had not been migrated at the last comparison.
8. Launch V1.3 using the V1.0 connection module and latest UI config; add exchange/non-exchange types and real master data. Verify all changes before allowing real transactions.

## Read-only discovery queries

```sql
USE SteelTransaction_POC;
SELECT s.name AS SchemaName,t.name AS TableName,SUM(p.rows) AS RowCount
FROM sys.tables t JOIN sys.schemas s ON t.schema_id=s.schema_id
JOIN sys.partitions p ON p.object_id=t.object_id
WHERE p.index_id IN (0,1) GROUP BY s.name,t.name ORDER BY t.name;

SELECT fk.name,OBJECT_NAME(fk.parent_object_id) AS ChildTable,
 OBJECT_NAME(fk.referenced_object_id) AS ParentTable FROM sys.foreign_keys fk;

SELECT TABLE_NAME,COLUMN_NAME,DATA_TYPE,CHARACTER_MAXIMUM_LENGTH,IS_NULLABLE,COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS ORDER BY TABLE_NAME,ORDINAL_POSITION;

SELECT OBJECT_NAME(object_id) AS TableName,name,seed_value,increment_value,last_value
FROM sys.identity_columns ORDER BY TableName;

SELECT SERVERPROPERTY('InstanceDefaultBackupPath') AS BackupPath,
 SERVERPROPERTY('InstanceDefaultDataPath') AS DataPath,
 SERVERPROPERTY('InstanceDefaultLogPath') AS LogPath;
SELECT name,physical_name,type_desc FROM sys.database_files;
```

Observed pre-copy counts: AuditV4 1; CustomersV2 2; DealAuditV2 0; DealsV2 0; Products 5; PurchaseInvoices 2; PurchaseItems 4; PurchaseServices 2; PurchasesV4 2; PurchaseTypes 3; SalesV4 1; Sellers 2; Services 4; SettlementTypes 3; Suppliers 3; Units 2; sysdiagrams 0.

## Backup and restore (historical procedure, paths redacted)

Replace placeholders with SQL Server-side paths, verify destination does not exist and use an authorized account. Do not use WITH REPLACE.

```sql
USE master;
BACKUP DATABASE SteelTransaction_POC TO DISK=N'<backup-path>\\SteelTransaction_POC_Pilot.bak'
WITH COPY_ONLY,CHECKSUM,COMPRESSION,STATS=10;
RESTORE VERIFYONLY FROM DISK=N'<backup-path>\\SteelTransaction_POC_Pilot.bak' WITH CHECKSUM;
RESTORE FILELISTONLY FROM DISK=N'<backup-path>\\SteelTransaction_POC_Pilot.bak';
RESTORE DATABASE SteelTransaction_PROD FROM DISK=N'<backup-path>\\SteelTransaction_POC_Pilot.bak'
WITH MOVE N'SteelTransaction_POC' TO N'<data-path>\\SteelTransaction_PROD.mdf',
MOVE N'SteelTransaction_POC_log' TO N'<log-path>\\SteelTransaction_PROD_log.ldf',RECOVERY,STATS=10;
SELECT name,state_desc,create_date FROM sys.databases WHERE name IN ('SteelTransaction_POC','SteelTransaction_PROD');
```

Reported restore: 794 pages processed, success, both databases ONLINE. VERIFYONLY is not a substitute for a recurring restore test.

## Historical cleanup and migration

Cleanup was proposed for the newly restored, test-only PROD database in this order: AuditV4, SalesV4, PurchasesV4, DealAuditV2, DealsV2, PurchaseServices, PurchaseItems, PurchaseInvoices. The final zero-row verification was not supplied. Never repeat this cleanup against live transactions. Identity counters were intentionally not reset.

The actual V1 migration adds ProductCategories, ProductSubcategories, nullable Products.SubcategoryID and SizeName, then adds ManualInvoiceNo, Notes, Quantity2, Rate2, dual-line CHECK constraint, TotalQuantity and TotalAmount to PurchasesV4 and SalesV4. It uses a transaction and existence checks; partial schema drift still needs review. Apply the original migrate.sql after backup, in the explicitly selected database. Do not run master_prod.sql after real transactions exist: it deletes and reseeds selected masters and is intended for initial setup only.

```sql
USE SteelTransaction_PROD;
INSERT dbo.PurchaseTypes(TypeName)
SELECT v.TypeName FROM (VALUES(N'بورسی'),(N'غیر بورسی')) v(TypeName)
WHERE NOT EXISTS(SELECT 1 FROM dbo.PurchaseTypes p WHERE p.TypeName=v.TypeName);

SELECT c.CategoryName,s.SubcategoryName,p.SizeName,p.ProductCode,p.ProductName
FROM dbo.Products p JOIN dbo.ProductSubcategories s ON p.SubcategoryID=s.SubcategoryID
JOIN dbo.ProductCategories c ON s.CategoryID=c.CategoryID ORDER BY c.CategoryName,s.SubcategoryName,p.ProductCode;
```

Master data imports use Unicode N-prefixed values, INSERT SELECT with NOT EXISTS, and transactions. Product codes are temporary; customers and suppliers use normalized names. Existing inactive supplier matches are not automatically reactivated. Old sample masters were not comprehensively removed.

## Environment verification

```sql
USE master;
SELECT name,state_desc,
 COL_LENGTH(name+'.dbo.PurchasesV4','ManualInvoiceNo') AS ManualNoBytes,
 COL_LENGTH(name+'.dbo.PurchasesV4','Notes') AS NotesBytes,
 COL_LENGTH(name+'.dbo.PurchasesV4','Quantity2') AS Quantity2Bytes,
 COL_LENGTH(name+'.dbo.PurchasesV4','TotalAmount') AS AmountBytes,
 OBJECT_ID(name+'.dbo.ProductCategories','U') AS CategoryObject
FROM sys.databases WHERE name IN ('SteelTransaction_POC','SteelTransaction_PROD');
```

Check both purchase and sale schemas, constraints and master data before deployment. Column existence alone does not prove readiness.

## CMD launch and troubleshooting

```cmd
cd /d C:\path\to\SteelTransactionSystem
.venv\Scripts\activate.bat
set STEEL_DB=SteelTransaction_POC
echo %STEEL_DB%
python -m streamlit run app_v1.py --server.address 0.0.0.0 --server.port 8501
```

For production, stop the app and set STEEL_DB=SteelTransaction_PROD only after acceptance. Browse http://localhost:8501 or the authorized LAN host address. If PowerShell blocks Activate.ps1, use CMD or invoke `.venv\Scripts\python.exe` directly. The reported `No module named streamlit` occurred because global Python 3.15 was used after activation failed. Do not weaken execution policy unnecessarily. Missing dbo.CustomersV2/DealAuditV2 means verify selected database and schema setup. Missing exchange options means seed PurchaseTypes. Missing product options means verify hierarchy and IsActive. Sidebar CSS may require adjustment after Streamlit upgrades.
