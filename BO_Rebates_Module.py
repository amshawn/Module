"""
Description: Functions used on the "Rebates tab" for  custom fields and quote tables

Input:
Output:

Dev: Rowyn Chengalanee, 12/06/2021, US 1537
	 Shawn Yong, 10/08/2021, US 2215
"""
from Scripting.QuoteTables import AccessLevel

def rebatesCheckbox(qTable):
	'''
	Control check on the checkbox column in Rebates table
	'''
	from Scripting.QuoteTables import AccessLevel
	checkList = []

	# set the index for the first row/line
	idx = 0
	for r in qTable.Rows:
		for c in r.Cells:
			if c.ColumnName == "IS_SELECTED":
				if c.Value == True:
					checkList.append(idx)
					#break
				else:
					# hide the cell
					c.AccessLevel = AccessLevel.Hidden
					idx += 1

	if not checkList:
		for row in qTable.Rows:
			for cell in row.Cells:
				if cell.ColumnName == "IS_SELECTED":
					cell.AccessLevel = AccessLevel.Editable

	qTable.Save()

#rules on rebate recipient type
def ruleOnRecpt(Quote, rebTypes):
	agrType = "1"
	for attr in Quote.GetCustomField('MG_H_AGREEMENTTYPE').AttributeValues:
		if attr.DisplayValue == Quote.GetCustomField('MG_H_AGREEMENTTYPE').Content:
			agrType = attr.ValueCode
			break

	if rebTypes.IS_CUSTGP: #rebate type is customer group
		#show rebate recipient type
		Quote.CustomFields.AllowValueByValueCode("BO_CF_RCPT_OPT", "ALL")
		#hide rebate recipient type
		Quote.CustomFields.DisallowValueByValueCode("BO_CF_RCPT_OPT", "1")
		#set default value
		Quote.CustomFields.SelectValueByValueCode("BO_CF_RCPT_OPT", "ALL")
		#set as required
		Quote.CustomFields.SetRequired("BO_CF_RCPT_OPT")
		#hide rebate recipient = sold-to
		Quote.CustomFields.Disallow("BO_CF_REBATE_RECIPIENT")
	else:
		#hide rebate recipient type
		Quote.CustomFields.DisallowValueByValueCode("BO_CF_RCPT_OPT", "ALL")
		#show rebate recipient type
		Quote.CustomFields.AllowValueByValueCode("BO_CF_RCPT_OPT", "1")
		#set default value
		Quote.CustomFields.SelectValueByValueCode("BO_CF_RCPT_OPT", "1")
		#reset validation Message
		Quote.QuoteTables["BO_SOLDTO"].ExecuteValidations()
		if agrType == "1": #offer agreement type = sold-to
			Quote.CustomFields.Allow("BO_CF_REBATE_RECIPIENT")
		else: #offer agreement type = end customer
			Quote.CustomFields.Disallow("BO_CF_REBATE_RECIPIENT")

#rules on rebate amount/percentage
def ruleOnRebAmt(Quote, codeType):
	if codeType == '%':
		#hide amount
		Quote.CustomFields.Disallow('BO_CF_REBATE_AMOUNT')
		#show percentage
		Quote.CustomFields.Allow('BO_CF_REBATE_PERC')
		#set as required
		Quote.CustomFields.SetRequired("BO_CF_REBATE_PERC")
	elif codeType == 'Q':
		#show amount
		Quote.CustomFields.Allow('BO_CF_REBATE_AMOUNT')
		#hide percentage
		Quote.CustomFields.Disallow('BO_CF_REBATE_PERC')
		#set as required
		Quote.CustomFields.SetRequired("BO_CF_REBATE_AMOUNT")

#rules on rebate amount/percentage columns
def ruleOnRebAmtCol(table, codeType):
	# check which column should be visible
	if codeType == '%':
		# hides column "Scale Amount" in Rebates Scale
		table.GetColumnByName('AMOUNT').AccessLevel = AccessLevel.Hidden
		table.GetColumnByName('PERC').AccessLevel   = AccessLevel.Editable
	elif codeType == 'Q':
		# hides column "Scale Percentage" in Rebates Scale
		table.GetColumnByName('PERC').AccessLevel   = AccessLevel.Hidden
		table.GetColumnByName('AMOUNT').AccessLevel = AccessLevel.Editable

#rules on exclusions for the rebate accumulation
def showExclSec(Quote, show):
	if show:
		# Show Inclusion and exclusions
		Quote.CustomFields.Allow('BO_CF_SEC_REBACC')
		Quote.CustomFields.Allow('BO_CF_OBJECT')
		Quote.QuoteTables['BO_INCL_TBL'].AccessLevel = AccessLevel.Editable
	else:
		# Hide Inclusion and exclusions
		Quote.CustomFields.Disallow('BO_CF_SEC_REBACC')
		Quote.CustomFields.Disallow('BO_CF_OBJECT')
		Quote.QuoteTables['BO_INCL_TBL'].AccessLevel = AccessLevel.Hidden

#rules to show hide rebate scales
def showScale(Quote, table, codeType, show):
	if show:
		# reset quote table
		#table.Rows.Clear()
		# Hide Rebate Amount customField
		Quote.CustomFields.Disallow('BO_CF_REBATE_AMOUNT')
		# Hide Rebate Percentage customField
		Quote.CustomFields.Disallow('BO_CF_REBATE_PERC')
		#show rebate scale
		table.AccessLevel = AccessLevel.Editable
		# check which column should be visible
		ruleOnRebAmtCol(table, codeType)
	else:
		#show rebate amount
		ruleOnRebAmt(Quote, codeType)
		# Hide Rebate Scale table
		table.AccessLevel = AccessLevel.Hidden

def rebateScaleVisibility(rebateScaleTable, rebateType, Quote):
	'''
	Changes the behaviour and visibility of columns in the quote table 'Rebate Scale'
	Changes the visibility of custom field 'Rebate Amount'
	'''

	if rebateType != "":
		# build sql query based on rebate type selected
		sqlQuery = "SELECT * FROM BO_REBATE_TYPE WHERE KEY_COMBO = '%s'"

		# call sql query & store values
		rebTypes  = SqlHelper.GetFirst(sqlQuery%rebateType)
		if rebTypes:
			#get conditional/unconditional
			checkCond = rebTypes.COND_UNCOND
			# strip the last value
			codeType = rebTypes.TYPE[-1]
			#set rebate recipient as mandatory
			ruleOnRecpt(Quote, rebTypes)
			# check if conditional or unconditional
			if checkCond == "Unconditional":
				#hide rebate scale
				showScale(Quote, rebateScaleTable, codeType, False)
				# Hide Exclusions for the rebate accumulation
				showExclSec(Quote, False)

			elif checkCond == "Conditional":
				#show rebate scale
				showScale(Quote, rebateScaleTable, codeType, True)
				# Show Exclusions for the rebate accumulation
				showExclSec(Quote, True)
		else:
			Trace.Write("[WARNING] Could not find entries in table <BO_REBATE_TYPE>")

	else:
		# hide the rebate percentage
		Quote.CustomFields.Disallow('BO_CF_REBATE_PERC')
		# hide scale
		rebateScaleTable.AccessLevel = AccessLevel.Hidden

	rebateScaleTable.Save()
	Quote.Save()


def rebateCodeType(rebateType):
	# build sql query based on rebate type selected
	sqlQuery    	= "SELECT COND_UNCOND,TYPE FROM BO_REBATE_TYPE WHERE KEY_COMBO = '%s'"

	# call sql query & store values
	checkCond   	= SqlHelper.GetFirst(sqlQuery%rebateType).COND_UNCOND
	codeType   		= SqlHelper.GetFirst(sqlQuery%rebateType).TYPE
	# strip the last value
	codeTypeShort 	= codeType[-1]

	return checkCond, codeType, codeTypeShort


def clearCustomFields(Quote):
	Quote.GetCustomField('BO_CF_NAME_OUTPUT').Content       = ""
	Quote.GetCustomField('BO_CF_REBATE_RECIPIENT').Content  = ""
	Quote.GetCustomField('BO_CF_VALIDITY_START').Content    = ""
	Quote.GetCustomField('BO_CF_VALIDITY_END').Content      = ""
	Quote.GetCustomField('BO_CF_PAY_CURRENCY').Content      = ""
	Quote.GetCustomField('BO_CF_RCPT_OPT').Content  		= ""
	Quote.GetCustomField('BO_CF_SETTLE_PERIOD').Content     = ""
	Quote.GetCustomField('BO_CF_SAP_NUM').Content      		= ""
	Quote.GetCustomField('BO_CF_VALID_UNTIL').Content      	= ""
	Quote.GetCustomField('BO_CF_UNIT').Content      		= ""
	Quote.GetCustomField('BO_CF_REBATE_PERC').Content      	= ""
	Quote.GetCustomField('BO_CF_REBATE_AMOUNT').Content     = ""
	Quote.CustomFields.SelectValueByValueCode("BO_CF_SETTLE_PERIOD", "0")

def rebateMsg(rebateType, Quote):
	codeTypeShort = rebateCodeType(rebateType)[2]
	if codeTypeShort == "%":
		Quote.GetCustomField('BO_CF_REBATE_MSG').Visible  = True
	else:
		Quote.GetCustomField('BO_CF_REBATE_MSG').Visible  = False



def checkDoubles(rebateType, periodicRebateTable):
	# Rebates already added in table
	periodicRebateList = []

	# Add the rebates to List
	for r in periodicRebateTable.Rows:
		for c in r.Cells:
			if c.ColumnName == "REBATE_TYPE":
				periodicRebateList.append(c.Value.decode('utf-8','ignore'))

	# Compare the rebate selected to those in table
	if rebateType in periodicRebateList:
		rebateDouble = True
	else:
		rebateDouble = False

	return rebateDouble


def rebateScaleDict(rebateScaleTable):
	# rebateScaleTable = Quote.QuoteTables['BO_REBATE_SCALE']
	# periodicRebateTable = Quote.QuoteTables['BO_REBATES']

	rebateScaleDict = dict()

	idx = 0
	for rows in rebateScaleTable.Rows:
		rebateScaleDict[idx] = {}
		for cell in rows.Cells:
			if cell.ColumnName == "AMOUNT":
				rebateScaleDict[idx][cell.ColumnName] = float(cell.Value)
			if cell.ColumnName == "QUANTITY":
				rebateScaleDict[idx][cell.ColumnName] = int(cell.Value)
			if cell.ColumnName == "PERC":
				rebateScaleDict[idx][cell.ColumnName] = float(cell.Value)
		idx += 1

	return rebateScaleDict

#2215 Shawn-------------------------------------------------------------------->
from Scripting.QuoteTables import AccessLevel

#get defaulted variable from custom table
def getVariable(name):
    variableTable = SqlHelper.GetFirst("""
    SELECT *
    FROM MG_VARIANT_VARIABLE
    WHERE NAME = '{name}'
    """.format(name=name)
    )
    if variableTable != None:
        var = { "TYPE": variableTable.TYPE, "LOW": variableTable.LOW, "HIGH": variableTable.HIGH }
    else:
        var = { "TYPE": "", "LOW": "", "HIGH": "" }
    return var

#get defaulted variable from custom table
def getVariableList(name):
    table = SqlHelper.GetList("""
    SELECT *
    FROM MG_VARIANT_VARIABLE
    WHERE NAME = '{name}'
    """.format(name=name)
    )
    return table

#get mills
def getMill(materialCode):
	table = SqlHelper.GetList("""
	SELECT PLANT
	FROM BO_PRODUCTS
	WHERE MATERIAL IN {matCode}
	""".format(matCode=materialCode))
	return table

#format material codes to be used in SQL
def getMatCodes(value):
	matCode = value.split(",")
	matCode = str(matCode)
	matCode = '(' + matCode[1:]
	matCode = matCode[:len(matCode)-1] + ')'
	return matCode

#get sales brand description
def getSalesBrand(code):
	table = SqlHelper.GetFirst("""
	SELECT SALES_BRAND
	FROM BO_SALES_BRAND
	WHERE SALES_BRAND_CODE = '{code}'
	""".format(code=code))
	return table.SALES_BRAND if table else ""

#enables exclusion table --> iteration to incl table
def setExcl(Quote, objCode, obj):
	#get associated fields to custom fields
	variable  = getVariable(objCode)
	#get table name
	tableName = variable["LOW"]
	#get attribute name
	attrName  = variable["HIGH"]
	#get inclusion/exclusion table
	table     = Quote.QuoteTables[tableName]
	#populate table
	setExclTable(Quote, table, attrName, variable, objCode, obj)

#deletes exclusions values
def deleteRows(table, objCode):
	delList = []
	#get list of row ids to be deleted
	for row in table.Rows:
		if row["OBJECT_CODE"] == objCode:
			delList.append(row.Id)
	#delete rows
	for i in delList:
		table.DeleteRow(i)
	#save table
	table.Save()

#populate inclusion/exclusion table
def setExclTable(Quote, table, attrName, variable, objCode, obj):
	#clear old entries
	deleteRows(table, objCode)
	itemList = []
	for item in Quote.MainItems:
		#edit only price sheets
		if item.ParentRolledUpQuoteItem == "":
			#get product
			product = item.EditConfiguration()
#Data from Product Attributes---------------------------------------------------
			if variable["TYPE"] == "P": #Product attributes
				if product.Attr(attrName).SelectedValue:
					#get new row
					newRow = table.AddNewRow()
					#update new row
					newRow["OBJECT"] 	   = obj
					newRow["OBJECT_CODE"]  = objCode
					newRow["CODE"]         = product.Attr(attrName).SelectedValue.ValueCode
					newRow["TOPIC"]   	   = product.Attr(attrName).GetValue()
#Data from Product Containers---------------------------------------------------
			elif variable["TYPE"] == "S": #Product attributes
				attr, container, colName = attrName.split("|")
				if product.Attr(attr).SelectedValue:
					#get new row
					newRow = table.AddNewRow()
					#update new row
					newRow["OBJECT"]       = obj
					newRow["OBJECT_CODE"]  = objCode
					newRow["CODE"]    	   = product.Attr(attr).SelectedValue.ValueCode
					newRow["TOPIC"]   	   = product.Attr(attr).GetValue()
				for row in product.GetContainerByName(container).Rows:
					#get new row
					newRow = table.AddNewRow()
					newRow["OBJECT_CODE"]  = objCode
					newRow["CODE"]    	   = row[colName].ReferencingAttribute.SelectedValue.ValueCode
					newRow["TOPIC"]   	   = row[colName].Value
#Data from Product Containers---------------------------------------------------
			elif variable["TYPE"] == "T": #Product containers
				var = attrName.split("|")
				container = "BO_{partnumber}_SALES_GRADES_CONT".format(partnumber=item.PartNumber)
				for row in product.GetContainerByName(container).Rows:
					if len(var) > 1:
						itemList.append(row[var[0]] + "|" + row[var[1]])
					else:
						if attrName == "REELS_SHEETS":
							#update new row
							itemList.append(row[attrName] + "|" + getVariable(row[attrName])["LOW"])
						elif attrName == "GRAMMAGE": #get mills
							#get list of material codes to be use in sql
							matCode = getMatCodes(row[attrName])
							#get list of mills from material codes
							mills  = getMill(matCode)
							for mill in mills:
								itemList.append("" + "|" + mill.PLANT)
						elif attrName == "SALES_BRAND": #get sales brand
							itemList.append(row[attrName] + "|" + getSalesBrand(row[attrName]))
#Data from Items--------------------------------------------------------------->
			elif variable["TYPE"] == "Q":
				val = attrName.split("|")
				itemList.append(eval("item."+val[0]) + "|" + eval("item."+val[1]))
#Data from Items--------------------------------------------------------------->
	#delete duplicated
	itemList = list(dict.fromkeys(itemList))
	#set table
	count = 0
	for row in itemList:
		#get new row
		newRow = table.AddNewRow()
		if count == 0:
			newRow["OBJECT"] = obj
		newRow["OBJECT_CODE"]= objCode
		#update new row
		newRow["CODE"], newRow["TOPIC"]  = row.split("|")
		count += 1
	#save table
	table.Save()

#enables exclusion table --> iteration to incl table
def setExclCalc(Quote, objCode, obj):
	#get associated fields to custom fields
	variable  = getVariable(objCode)
	#get table name
	tableName = variable["LOW"]
	#get attribute name
	attrName  = variable["HIGH"]
	#get inclusion/exclusion table
	table     = Quote.QuoteTables[tableName + "_CALC"]
	#populate table
	setExclTable(Quote, table, attrName, variable, objCode, obj)

#2215 END---------------------------------------------------------------------->

#2215 END---------------------------------------------------------------------->
#Build Dictionary for:----------------------------------------------------------
"""
<ConditionScaleQty></ConditionScaleQty>
<Rate></Rate>
"""
def getConditionScale(scale, type):
	conditionScale = dict()
	conditionScale["ConditionScaleQty"] = scale["QUANTITY"]  #Condition scale quantity
	if type == "%":
		conditionScale["Rate"]			= scale["PERC"] * -1	  #Rate (condition amount or percentage)
	else:
		conditionScale["Rate"]			= scale["AMOUNT"] * -1
	return conditionScale

def getEmptyConditionScale():
	conditionScale = dict()
	conditionScale["ConditionScaleQty"] 	= ""
	conditionScale["Rate"]					= ""
	return conditionScale
#Build Dictionary for:----------------------------------------------------------
"""
<ConditionType></ConditionType>
<ScaleType></ScaleType>
<ScaleIndicator></ScaleIndicator>
<ScaleConditionUnit></ScaleConditionUnit>
<CalculationType></CalculationType>
<Rate></Rate>
<RateUnit></RateUnit>
<ConditionPricingUnit></ConditionPricingUnit>
<ConditionUnit></ConditionUnit>
<Material></Material>
<AccrualAmount></AccrualAmount>
<ConditionQtyScale>
	...
</ConditionQtyScale>
<ConditionValueScale>
	...
</ConditionValueScale>
"""
def getConditionItems(condType,		#Condition Type
					  scaleType,	#Scale Type; constant "A"
					  scaleInd,		#Scale basis indicator; constant "C"
					  scaleUnit,	#Condition scale unit of measure
					  calcType,		#Calculation type for condition
					  rate,			#Rate (condition amount or perc
					  rateUnit,		#Rate unit (currency or percent
					  condPriceUnit,#Condition pricing unit
					  condUnit,		#Condition unit
					  mat,			#Material for rebate settlement; constant "SETTLEMENT MAT"
					  accAmt,		#Accrual Amount
					  scales,		#rebate scale table
					  process		#process; ex:CREATE or UPDATE
					 ):
	conditionItems = dict()
	conditionItems["ConditionType"] 		 	 = ""
	conditionItems["ScaleType"] 		 	 	 = ""
	conditionItems["ScaleIndicator"] 	 		 = ""
	conditionItems["ScaleConditionUnit"] 		 = ""
	conditionItems["CalculationType"] 		 	 = ""
	conditionItems["Rate"] 					 	 = ""
	conditionItems["RateUnit"] 				 	 = ""
	conditionItems["ConditionPricingUnit"]   	 = ""
	conditionItems["ConditionUnit"] 		 	 = ""
	conditionItems["Material"] 				  	 = ""
	conditionItems["AccrualAmount"] 	 	 	 = ""
	if process == "UPDATE":
		conditionItems["ConditionType"] 		 = condType
		if scales.Rows.Count > 0:
			conditionItems["ScaleType"] 		 = scaleType
			conditionItems["ScaleIndicator"] 	 = scaleInd
			conditionItems["ScaleConditionUnit"] = scaleUnit
		conditionItems["CalculationType"] 		 = calcType
		conditionItems["Rate"] 					 = rate
		if condType[len(condType)-1] == "%":
			conditionItems["ConditionPricingUnit"]   = ""
			conditionItems["RateUnit"] 				 = "P1"
			conditionItems["ConditionUnit"] 		 = "P1"
		else:
			conditionItems["ConditionPricingUnit"]   = condPriceUnit
			conditionItems["RateUnit"] 				 = rateUnit
			conditionItems["ConditionUnit"] 		 = condUnit
		conditionItems["Material"] 				 = mat
		conditionItems["AccrualAmount"] 	 	 = accAmt

		multiScale = list()

		#build scale
		for scale in scales.Rows:
			multiScale.append(getConditionScale(scale, condType[len(condType)-1]))

		conditionItems["ConditionQtyScale"] 	 = multiScale
		conditionItems["ConditionValueScale"]    = getEmptyConditionScale()

	else:
		conditionItems["ConditionQtyScale"]			 = getEmptyConditionScale()
		conditionItems["ConditionValueScale"]		 = getEmptyConditionScale()
	return conditionItems
#Build Dictionary for:----------------------------------------------------------
"""
<ValidFrom>20210618</ValidFrom>
<ValidTo>20211231</ValidTo>
<ConditionsItems>
	...
</ConditionsItems>
"""
def getConditionHeader(validFrom, 	 #rebate valid from
					   validTo,   	 #rebate valid to
					   condType,  	 #Condition Type
					   scaleType, 	 #Scale Type; constant "A"
					   scaleInd,  	 #Scale basis indicator; constant "C"
					   scaleUnit, 	 #Condition scale unit of measure
					   calcType,	 #Calculation type for condition
					   rate,		 #Rate (condition amount or perc
					   rateUnit,	 #Rate unit (currency or percent
					   condPriceUnit,#Condition pricing unit
					   condUnit,	 #Condition unit
					   mat,			 #Material for rebate settlement; constant "SETTLEMENT MAT"
					   accAmt,		 #Accrual Amount
					   scale,		 #rebate scale table
					   process		 #process; ex:CREATE or UPDATE
					  ):
	conditionHeader = dict()
	conditionHeader["ValidFrom"] 	   	   = ""
	conditionHeader["ValidTo"] 		   	   = ""
	if process == "UPDATE":
		conditionHeader["ValidFrom"] 	   = str(validFrom)
		conditionHeader["ValidTo"] 		   = str(validTo)
	conditionHeader["ConditionsItems"] 	   = getConditionItems(condType,	 #Condition Type
															   scaleType,	 #Scale Type; constant "A"
															   scaleInd,	 #Scale basis indicator; constant "C"
															   scaleUnit,	 #Condition scale unit of measure
															   calcType,	 #Calculation type for condition
															   rate,		 #Rate (condition amount or perc
															   rateUnit,	 #Rate unit (currency or percent
															   condPriceUnit,#Condition pricing unit
															   condUnit,	 #Condition unit
															   mat,			 #Material for rebate settlement; constant "SETTLEMENT MAT"
															   accAmt,		 #Accrual Amount
															   scale,		 #rebate scale table
															   process		 #process; ex:CREATE or UPDATE
															  )
	return conditionHeader
#Build Dictionary for:----------------------------------------------------------
"""
<Function></Function>
<TagColumn></TagColumn>
<TextLine></TextLine>
"""
def getRebateItem(func, 	#Function; constant "009"
				  tagCol,   #Tag column; constant "*"
				  txtLine,  #Text line
				  process   #process; ex:CREATE or UPDATE
				 ):
	rebateItem = dict()
	rebateItem["Function"]  	= ""
	rebateItem["TagColumn"] 	= ""
	rebateItem["TextLine"]  	= ""
	if process == "CREATE":
		rebateItem["Function"]  = func
		rebateItem["TagColumn"] = tagCol
		rebateItem["TextLine"]  = txtLine
	return rebateItem
#Build Dictionary for:----------------------------------------------------------
"""
<Function></Function>
<ApplicationObject></ApplicationObject>
<TextID></TextID>
<LanguageKey></LanguageKey>
<RebateItem>
	...
</RebateItem>
"""
def getCondRebateHeader(func, 	 #Function; constant "009"
						appObj,  #Texts: Application Object; constant "KONA"
						txtId,   #Text ID; constant "ZAGR"
						langKey, #Language Key; constant "E"
						tagCol,  #Tag column; constant "*"
						txtLine, #Text line
						process	 #process; ex:CREATE or UPDATE
						):
	conditionHeader = dict()
	conditionHeader["Function"] 	      	 = ""
	conditionHeader["ApplicationObject"]  	 = ""
	conditionHeader["TextID"] 	   		  	 = ""
	conditionHeader["LanguageKey"] 	   	 	 = ""
	if process == "CREATE":
		conditionHeader["Function"] 	     = func
		conditionHeader["ApplicationObject"] = appObj
		conditionHeader["TextID"] 	   		 = txtId
		conditionHeader["LanguageKey"] 	   	 = langKey
	conditionHeader["RebateItem"] 	   	 	 = getRebateItem(func, 	  #Function; constant "009"
															 tagCol,  #Tag column; constant "*"
															 txtLine, #Text line
															 process  #process; ex:CREATE or UPDATE
															)
	return conditionHeader
#Build Dictionary for:----------------------------------------------------------
"""
<Rebate>
  <SalesOrg></SalesOrg>
  <DistChan></DistChan>
  <Division></Division>
  <AgreementNum></AgreementNum>
  <AgreementType></AgreementType>
  <RefDocNum></RefDocNum>
  <RebateRecipient></RebateRecipient>
  <CurrencyKey></CurrencyKey>
  <AgrValidFrom></AgrValidFrom>
  <AgrValidTo></AgrValidTo>
  <ConditionHeader>
	....
  </ConditionHeader>
</Rebate>
"""
def getRebate(sOrg,			#sales organisation
			  distCh, 		#distribution channell
			  div,			#division
			  agrNum,		#agreement number
			  agrType,		#agreement type
			  refDocNum,	#reference number
			  recipient,	#rebate recipient
			  currency,		#currency
			  agrValidFrom,	#agreement valid from
			  agrValidTo,	#agreement valid to
			  validFrom,	#rebate valid from
			  validTo,		#rebate valid to
			  func, 		#Function; constant "009"
			  appObj, 		#Texts: Application Object; constant "KONA"
			  txtId,  		#Text ID; constant "ZAGR"
			  langKey, 		#Language Key; constant "E"
			  tagCol,  		#Tag column; constant "*"
			  txtLine,  	#Text line
			  process		#process; ex:CREATE or UPDATE
			 ):
	rebate = dict()
	rebate["SalesOrg"] 		  	  = ""
	rebate["DistChan"] 		 	  = ""
	rebate["Division"] 		  	  = ""
	#BRIAN MOD
 	#rebate["AgreementNum"]    	  = ""
	rebate["AgreementType"]   	  = ""
 	rebate["RefDocNum"] 	  	  = refDocNum
	rebate["RebateRecipient"] 	  = ""
	rebate["CurrencyKey"] 	  	  = ""
	rebate["AgrValidFrom"] 	  	  = ""
	rebate["AgrValidTo"]	  	  = ""
	if process == "CREATE":
		rebate["SalesOrg"] 		  = sOrg
		rebate["DistChan"] 		  = distCh
		rebate["Division"] 		  = div
		#BRIAN MOD
  		#rebate["AgreementNum"]    = agrNum
		rebate["AgreementType"]   = agrType
		rebate["RebateRecipient"] = recipient
		rebate["CurrencyKey"] 	  = currency
		rebate["AgrValidFrom"] 	  = agrValidFrom
		rebate["AgrValidTo"]	  = agrValidTo
	rebate["ConditionHeader"] 	  = getCondRebateHeader(func, 	 #Function; constant "009"
														appObj,  #Texts: Application Object; constant "KONA"
														txtId,   #Text ID; constant "ZAGR"
														langKey, #Language Key; constant "E"
														tagCol,  #Tag column; constant "*"
														txtLine, #Text line
														process	 #process; ex:CREATE or UPDATE
														)
	return rebate
#Build Dictionary for:----------------------------------------------------------
"""
<ConditionKey>
	<Usage></Usage>
	<ConditionTable></ConditionTable>
	<Application></Application>
	<ConditionType></ConditionType>
	<SalesOrg></SalesOrg>
	<DistChan></DistChan>
	<Division></Division>
	<VariableKey></VariableKey>
	<Rebate>
		...
	</Rebate>
	<ConditionHeader>
		...
	</ConditionHeader>
</ConditionKey>
"""
def getConditionKey(usage,		  #Usage of the condition table; constant "E"
					tableNum,	  #condition table
					app,		  #Application; constant"V"
					condType, 	  #condition type
					variableKey,  #variable key
					sOrg,		  #sales organisation; Constant "1000"
					distCh,		  #disctribution channel; Constant "10"
					div,		  #division; constant "PG"
					agrNum,		  #Agreement Number
					agrType,	  #Agreement type
					refDocNum,	  #Reference Document Number
					recipient,	  #Rebate recipient
					currency,	  #Currency Key
					agrValidFrom, #agreement valid from
					agrValidTo,	  #agreement valid to
					validFrom,	  #rebate valid from
					validTo,	  #rebate valid to
					func, 		  #Function; constant "009"
					appObj, 	  #Texts: Application Object; constant "KONA"
					txtId,  	  #Text ID; constant "ZAGR"
					langKey, 	  #Language Key; constant "E"
					tagCol,  	  #Tag column; constant "*"
					txtLine, 	  #Text line
					scaleType, 	  #Scale Type; constant "A"
					scaleInd,  	  #Scale basis indicator; constant "C"
					scaleUnit, 	  #Condition scale unit of measure
					calcType,	  #Calculation type for condition
					rate,		  #Rate (condition amount or perc
					rateUnit,	  #Rate unit (currency or percent
					condPriceUnit,#Condition pricing unit
					condUnit,	  #Condition unit
					mat,		  #Material for rebate settlement; constant "SETTLEMENT MAT"
					accAmt,		  #Accrual Amount
					scale,		  #rebate scale table
					process		  #process; ex:CREATE or UPDATE
					):
	conditionKey = dict()
	conditionKey["Usage"]		  		= ""
	conditionKey["ConditionTable"]		= ""
	conditionKey["Application"]	  		= ""
	conditionKey["ConditionType"] 		= ""
	conditionKey["SalesOrg"] 	  		= ""
	conditionKey["DistChan"] 	  		= ""
	conditionKey["Division"] 	  		= ""
	conditionKey["VariableKey"]    		= ""
	if process == "UPDATE":
		conditionKey["Usage"]		  	= usage
		conditionKey["ConditionTable"]	= tableNum
		conditionKey["Application"]	  	= app
		conditionKey["ConditionType"] 	= condType
		conditionKey["SalesOrg"] 	  	= sOrg
		conditionKey["DistChan"] 	  	= distCh
		conditionKey["Division"] 	  	= div
		conditionKey["VariableKey"]    	= variableKey
	conditionKey["Rebate"] 		  		= getRebate(sOrg,		 #sales organisation; Constant "1000"
													distCh,		 #disctribution channel; Constant "10"
													div,		 #division; constant "PG"
													agrNum,		 #agreement number
													agrType,	 #agreement type
													refDocNum,	 #reference number
													recipient,	 #rebate recipient
													currency,	 #currency
													agrValidFrom,#agreement valid from
													agrValidTo,	 #agreement valid to
													validFrom,	 #rebate valid from
													validTo,	 #rebate valid to
													func, 		 #Function; constant "009"
													appObj, 	 #Texts: Application Object; constant "KONA"
													txtId,  	 #Text ID; constant "ZAGR"
													langKey, 	 #Language Key; constant "E"
													tagCol,  	 #Tag column; constant "*"
													txtLine,  	 #Text line
													process		 #process; ex:CREATE or UPDATE
													)
	conditionKey["ConditionHeader"] 	= getConditionHeader(validFrom,    #rebate valid from
															 validTo,      #rebate valid to
															 condType,     #Condition Type
															 scaleType,    #Scale Type; constant "A"
															 scaleInd,     #Scale basis indicator; constant "C"
															 scaleUnit,    #Condition scale unit of measure
															 calcType,	   #Calculation type for condition
															 rate,		   #Rate (condition amount or perc
															 rateUnit,	   #Rate unit (currency or percent
															 condPriceUnit,#Condition pricing unit
															 condUnit,	   #Condition unit
															 mat,		   #Material for rebate settlement; constant "SETTLEMENT MAT"
															 accAmt,	   #Accrual Amount
															 scale,		   #rebate scale table
															 process	   #process; ex:CREATE or UPDATE
															)
	return conditionKey
#Build Dictionary for:----------------------------------------------------------
"""
<ConditionKey>
	....
</ConditionKey>
"""
def getRebateXml(conditionKey):
	rebateXml = dict()
	rebateXml["ConditionKey"] = conditionKey
	return rebateXml
#get rebate conditions details from rebates conditions table--------------------
def getRebateCondition(condType,#condition code; ex: Z*%, Z*Q
					   agrType, #agreement type code; ex: 1=Sold-to, 2=End Customer
					   isEndObj,#contains end use object; ex: True/False
					   isSb2,	#contains sales brand; ex: True/False
					   isGroup,	#contains customer hierarchy; ex: True/False
					   isRlSh	#contains reels sheets; ex: True/False
					  ):
	table = SqlHelper.GetFirst("""
	SELECT *
	FROM BO_REBATE_CONDITIONS
	WHERE COND_TYPE = '{condCode}'
	AND AGR_TYPE 	= '{agrType}'
	AND IS_SB2		= '{saleBrd}'
	AND IS_GROUP	= '{custHie}'
	AND IS_RLSH		= '{reelSh}' """.format(condCode= condType,
											agrType = agrType,
											saleBrd = isSb2,
											custHie = isGroup,
											reelSh  = isRlSh))
	return table.TABLE_NUM, table.IS_ENDOBJ if table else ""

#get defaulted variable from custom table
def getVariable(name):
	variableTable = SqlHelper.GetFirst("""
	SELECT *
	FROM MG_VARIANT_VARIABLE
	WHERE NAME = '{name}'
	""".format(name=name)
	)
	if variableTable != None:
		var = { "TYPE": variableTable.TYPE, "LOW": variableTable.LOW, "HIGH": variableTable.HIGH }
	else:
		var = { "TYPE": "", "LOW": "", "HIGH": "" }
	return var

#get rebate type code
def getRebateCode(condName):
	table = SqlHelper.GetFirst("""
	SELECT *
	FROM BO_REBATE_TYPE
	WHERE KEY_COMBO = '{0}'
	""".format(condName))
	return table.TYPE, table.IS_CUSTGP if table else ""

def getJson(Quote, refDocNum):
	#get recipient type
	for attr in Quote.GetCustomField('BO_CF_RCPT_OPT').AttributeValues:
		if attr.DisplayValue == Quote.GetCustomField('BO_CF_RCPT_OPT').Content:
			recipientType = attr.ValueCode
			break
	#------------------------------------------------------------------------------
	if recipientType == "1": #rebate does not have customer group
		#Define condition key list which will contain all rebateScaleDict conditions
		conditionKey = list()
		#get Reels/Sheets, end use objects and Sales Brands
		matTypes 	= list()
		brands 		= list()
		endObjs		= list()
	#get common constants-----------------------------------------------------------
		sOrg 		= getVariable("SALES_ORG")["LOW"]
		distCh 		= getVariable("DIS_CHN")["LOW"]
		div 		= getVariable("DIVISION")["LOW"]
		usage 	 	= getVariable("USAGE")["LOW"]
		app 	 	= getVariable("APPLICATION")["LOW"]
		appObj		= getVariable("APPLICATION_OBJECT")["LOW"]
		mat		 	= getVariable("MATERIAL")["LOW"]
		scaleType	= getVariable("SCALE_TYPE")["LOW"]
		scaleInd 	= getVariable("SCALE_INDICATOR")["LOW"]
		func  	 	= getVariable("FUNCTION")["LOW"]
		txtId 	 	= getVariable("TEXT_ID")["LOW"]
		langKey	 	= getVariable("LANGUAGE_KEY")["LOW"]
		tagCol	 	= getVariable("TAG_COLUMN")["LOW"]
		#get Text line obsolete
		txtLine		= Quote.GetCustomField('BO_CF_NAME_OUTPUT').Content
	#get values from offer----------------------------------------------------------
		#condition code
		condName 	 = Quote.GetCustomField('BO_CF_REBATE_TYPE').Content
		#condition type
		condType, isGroup  = getRebateCode(condName)
		#rebate type agreement
		rebType = condType[:len(condType)-1]
		#Agreement Number
		agrNum	 	 = Quote.CompositeNumber
		#Agreement type
		agrType  	 = "1"
		for attr in Quote.GetCustomField('MG_H_AGREEMENTTYPE').AttributeValues:
			if attr.DisplayValue == Quote.GetCustomField('MG_H_AGREEMENTTYPE').Content:
				agrType = attr.ValueCode
				break
		#Rebate recipient
		if agrType == "1": #sold-to
			recipient= Quote.GetCustomField('BO_CF_REBATE_RECIPIENT').Content.split(",")[0]
		else: #end customer
			recipient= Quote.GetCustomField('BO_CF_END_CUSTOMER').Content.split(",")[0]
		#Currency Key
		currency 	 = Quote.GetCustomField('BO_CF_PAY_CURRENCY').Content
		#rebate valid from
		validFrom	 = UserPersonalizationHelper.CovertToDate(Quote.GetCustomField('BO_CF_VALIDITY_START').Content).ToString('yyyyMMdd')
		#rebate valid to
		validTo	 	 = UserPersonalizationHelper.CovertToDate(Quote.GetCustomField('BO_CF_VALIDITY_END').Content).ToString('yyyyMMdd')
		#Condition scale unit of measure
		scaleUnit	 = Quote.GetCustomField('BO_CF_UNIT').Content.split(" ")[1]
		#rebate scale table
		scale		 = Quote.QuoteTables["BO_REBATE_SCALE"]
		#accrual amount
		accAmt		 = 0
		#Calculation type for condition
		if condType[len(condType)-1] == "Q":
			#Quantity
			calcType = "C"
			#Rate (condition amount)
			rate	 = float(Quote.GetCustomField('BO_CF_REBATE_AMOUNT').Content if Quote.GetCustomField('BO_CF_REBATE_AMOUNT').Content else "0")
			accAmt	 = rate
			if scale.Rows.Count > 0:
				rate = scale.Rows[0]["AMOUNT"]
			#Accrual Amount
			for row in scale.Rows:
				if rate == 0:
					rate = row["AMOUNT"]
				if row["AMOUNT"] > accAmt:
					accAmt = row["AMOUNT"]
		else:
			#Percentage
			calcType = "A"
			#Rate (condition perc)
			rate	 = float(Quote.GetCustomField('BO_CF_REBATE_PERC').Content if Quote.GetCustomField('BO_CF_REBATE_PERC').Content else "0")
			accAmt	 = rate
			if scale.Rows.Count > 0:
				accAmt = scale.Rows[0]["PERC"]
				rate   = accAmt
			#Accrual Amount
			for row in scale.Rows:
				if row["PERC"] > accAmt:
					accAmt = row["PERC"]
		accAmt = accAmt * -1
		rate   = rate * -1
		#Rate unit (currency or percent
		rateUnit 	 = currency
		#Condition pricing unit
		condPriceUnit= "1"
		#Condition unit
		condUnit	 = scaleUnit
		#get Sales org/Distr ch/Div/
		salesOrg 	 = sOrg + distCh + div
	#get keys-----------------------------------------------------------------------
		for item in Quote.MainItems:
			#edit only price sheets
			if item.ParentRolledUpQuoteItem == "":
				#get product
				product = item.EditConfiguration()
				#get end use object
				endObjs.append(product.Attr("MG_END_CUSTOMER").SelectedValue)
				#get sales grade container
				container = "BO_{0}_SALES_GRADES_CONT".format(item.PartNumber)
				#get material type and Sales Brands
				for row in product.GetContainerByName(container).Rows:
					matTypes.append(row["REELS_SHEETS"])
				for row in product.GetContainerByName("BO_PRICING_CONT").Rows:
					if row["SALES_BRAND_CODE"] != "":
						brands.append(row["SALES_BRAND_CODE"])
		#delete duplicates
		matTypes  = list(dict.fromkeys(matTypes))
		brands    = list(dict.fromkeys(brands))
		endObjs   = list(dict.fromkeys(endObjs))
		isEndObj = isSb2 = isGroup = isRlSh  = False
		#does appendix #2 contains end use object
		if len(endObjs) > 0:
			isEndObj = True
		#does appendix #2 contains sales brand
		if len(brands) > 0:
			isSb2 = True
		#does appendix #2 contains material type
		if len(matTypes) > 0:
			isRlSh = True
		#get rebate conditions
		tableNum, isEndObj 	= getRebateCondition(condType, agrType, isEndObj, isSb2, isGroup, isRlSh)
		#get sold-to table
		soldTos = Quote.QuoteTables["BO_SOLDTO"]
	#build variable key-------------------------------------------------------------
		#1. add sales org
		variableKey = salesOrg
		#2. Sales org/Distr ch/Div/Sold-to/SB2/RL-SH
		for matType in matTypes:
			if isSb2:
				for brand in brands:
					for soldTo in soldTos.Rows:
						variableKey = salesOrg
						variableKey =  variableKey + brand + soldTo["SAPID"].zfill(10) + matType
						#add end customer if applicable
						if agrType == "3": #end customer
							#Sales org/Distr ch/Div/Sold-to/SB2/RL-SH/End User
							variableKey = salesOrg + endCust + brand + soldTo["SAPID"].zfill(10) + matType
							if isEndObj:
								for endObj in endObjs:
									#add end use object if applicable
									if isEndObj:
										variableKey = salesOrg + endCust + brand + soldTo["SAPID"].zfill(10) + endObj

										#build dictionary for condition key
										condKey = getConditionKey(usage,		#Usage of the condition table; constant "E"
																  tableNum,	  	#condition table
																  app,		  	#Application; constant"V"
																  condType, 	#condition type
																  variableKey,  #variable key
																  sOrg,		  	#sales organisation; Constant "1000"
																  distCh,		#disctribution channel; Constant "10"
																  div,				#division; constant "PG"
																  agrNum,		#Agreement Number
																  rebType,	  	#Agreement type
																  refDocNum,	#Reference Document Number
																  recipient,	#Rebate recipient
																  currency,	  	#Currency Key
																  validFrom, #agreement valid from
																  validTo,	#agreement valid to
																  validFrom,	#rebate valid from
																  validTo,		#rebate valid to
																  func, 		#Function; constant "009"
																  appObj, 	  	#Texts: Application Object; constant "KONA"
																  txtId,  	  	#Text ID; constant "ZAGR"
																  langKey, 	  	#Language Key; constant "E"
																  tagCol,		#Tag column; constant "*"
																  txtLine,		#Text line
																  scaleType, 	#Scale Type; constant "A"
																  scaleInd,  	#Scale basis indicator; constant "C"
																  scaleUnit, 	#Condition scale unit of measure
																  calcType,	  	#Calculation type for condition
																  rate,		  	#Rate (condition amount or perc
																  rateUnit,		#Rate unit (currency or percent
																  condPriceUnit,#Condition pricing unit
																  condUnit,		#Condition unit
																  mat,			#Material for rebate settlement; constant "SETTLEMENT MAT"
																  accAmt,		#Accrual Amount
																  scale,		#rebate scale table
																  "UPDATE"
																)
									else:
										#build dictionary for condition key
										condKey = getConditionKey(usage,		#Usage of the condition table; constant "E"
																  tableNum,	  	#condition table
																  app,		  	#Application; constant"V"
																  condType, 	#condition type
																  variableKey,  #variable key
																  sOrg,		  	#sales organisation; Constant "1000"
																  distCh,		#disctribution channel; Constant "10"
																  div,				#division; constant "PG"
																  agrNum,		#Agreement Number
																  rebType,	  	#Agreement type
																  refDocNum,	#Reference Document Number
																  recipient,	#Rebate recipient
																  currency,	  	#Currency Key
																  validFrom, #agreement valid from
																  validTo,	#agreement valid to
																  validFrom,	#rebate valid from
																  validTo,		#rebate valid to
																  func, 		#Function; constant "009"
																  appObj, 	  	#Texts: Application Object; constant "KONA"
																  txtId,  	  	#Text ID; constant "ZAGR"
																  langKey, 	  	#Language Key; constant "E"
																  tagCol,		#Tag column; constant "*"
																  txtLine,		#Text line
																  scaleType, 	#Scale Type; constant "A"
																  scaleInd,  	#Scale basis indicator; constant "C"
																  scaleUnit, 	#Condition scale unit of measure
																  calcType,	  	#Calculation type for condition
																  rate,		  	#Rate (condition amount or perc
																  rateUnit,		#Rate unit (currency or percent
																  condPriceUnit,#Condition pricing unit
																  condUnit,		#Condition unit
																  mat,			#Material for rebate settlement; constant "SETTLEMENT MAT"
																  accAmt,		#Accrual Amount
																  scale,		#rebate scale table
																  "UPDATE"
																)
										break
							else:
								#build dictionary for condition key
								condKey = getConditionKey(usage,		#Usage of the condition table; constant "E"
														  tableNum,	  	#condition table
														  app,		  	#Application; constant"V"
														  condType, 	#condition type
														  variableKey,  #variable key
														  sOrg,		  	#sales organisation; Constant "1000"
														  distCh,		#disctribution channel; Constant "10"
														  div,				#division; constant "PG"
														  agrNum,		#Agreement Number
														  rebType,	  	#Agreement type
														  refDocNum,	#Reference Document Number
														  recipient,	#Rebate recipient
														  currency,	  	#Currency Key
														  validFrom, #agreement valid from
														  validTo,	#agreement valid to
														  validFrom,	#rebate valid from
														  validTo,		#rebate valid to
														  func, 		#Function; constant "009"
														  appObj, 	  	#Texts: Application Object; constant "KONA"
														  txtId,  	  	#Text ID; constant "ZAGR"
														  langKey, 	  	#Language Key; constant "E"
														  tagCol,		#Tag column; constant "*"
														  txtLine,		#Text line
														  scaleType, 	#Scale Type; constant "A"
														  scaleInd,  	#Scale basis indicator; constant "C"
														  scaleUnit, 	#Condition scale unit of measure
														  calcType,	  	#Calculation type for condition
														  rate,		  	#Rate (condition amount or perc
														  rateUnit,		#Rate unit (currency or percent
														  condPriceUnit,#Condition pricing unit
														  condUnit,		#Condition unit
														  mat,			#Material for rebate settlement; constant "SETTLEMENT MAT"
														  accAmt,		#Accrual Amount
														  scale,		#rebate scale table
														  "UPDATE"
														)
						else:
							#build dictionary for condition key
							condKey = getConditionKey(usage,		#Usage of the condition table; constant "E"
													  tableNum,	  	#condition table
													  app,		  	#Application; constant"V"
													  condType, 	#condition type
													  variableKey,  #variable key
													  sOrg,		  	#sales organisation; Constant "1000"
													  distCh,		#disctribution channel; Constant "10"
													  div,				#division; constant "PG"
													  agrNum,		#Agreement Number
													  rebType,	  	#Agreement type
													  refDocNum,	#Reference Document Number
													  recipient,	#Rebate recipient
													  currency,	  	#Currency Key
													  validFrom, #agreement valid from
													  validTo,	#agreement valid to
													  validFrom,	#rebate valid from
													  validTo,		#rebate valid to
													  func, 		#Function; constant "009"
													  appObj, 	  	#Texts: Application Object; constant "KONA"
													  txtId,  	  	#Text ID; constant "ZAGR"
													  langKey, 	  	#Language Key; constant "E"
													  tagCol,		#Tag column; constant "*"
													  txtLine,		#Text line
													  scaleType, 	#Scale Type; constant "A"
													  scaleInd,  	#Scale basis indicator; constant "C"
													  scaleUnit, 	#Condition scale unit of measure
													  calcType,	  	#Calculation type for condition
													  rate,		  	#Rate (condition amount or perc
													  rateUnit,		#Rate unit (currency or percent
													  condPriceUnit,#Condition pricing unit
													  condUnit,		#Condition unit
													  mat,			#Material for rebate settlement; constant "SETTLEMENT MAT"
													  accAmt,		#Accrual Amount
													  scale,		#rebate scale table
													  "UPDATE"
													)
						conditionKey.append(condKey)
			else:
				for soldTo in soldTos.Rows:
					variableKey = salesOrg
					variableKey =  variableKey + matType + soldTo["SAPID"].zfill(10)
					#add end customer if applicable
					if agrType == "3": #end customer
						#Sales org/Distr ch/Div/Sold-to/SB2/RL-SH/End User
						variableKey = salesOrg + endCust + matType + soldTo["SAPID"].zfill(10)
						if isEndObj:
							for endObj in endObjs:
								#add end use object if applicable
								if isEndObj:
									variableKey = salesOrg + endCust + matType + soldTo["SAPID"].zfill(10) + endObj

									#build dictionary for condition key
									condKey = getConditionKey(usage,		#Usage of the condition table; constant "E"
															  tableNum,	  	#condition table
															  app,		  	#Application; constant"V"
															  condType, 	#condition type
															  variableKey,  #variable key
															  sOrg,		  	#sales organisation; Constant "1000"
															  distCh,		#disctribution channel; Constant "10"
															  div,				#division; constant "PG"
															  agrNum,		#Agreement Number
															  rebType,	  	#Agreement type
															  refDocNum,	#Reference Document Number
															  recipient,	#Rebate recipient
															  currency,	  	#Currency Key
															  validFrom, #agreement valid from
															  validTo,	#agreement valid to
															  validFrom,	#rebate valid from
															  validTo,		#rebate valid to
															  func, 		#Function; constant "009"
															  appObj, 	  	#Texts: Application Object; constant "KONA"
															  txtId,  	  	#Text ID; constant "ZAGR"
															  langKey, 	  	#Language Key; constant "E"
															  tagCol,		#Tag column; constant "*"
															  txtLine,		#Text line
															  scaleType, 	#Scale Type; constant "A"
															  scaleInd,  	#Scale basis indicator; constant "C"
															  scaleUnit, 	#Condition scale unit of measure
															  calcType,	  	#Calculation type for condition
															  rate,		  	#Rate (condition amount or perc
															  rateUnit,		#Rate unit (currency or percent
															  condPriceUnit,#Condition pricing unit
															  condUnit,		#Condition unit
															  mat,			#Material for rebate settlement; constant "SETTLEMENT MAT"
															  accAmt,		#Accrual Amount
															  scale,		#rebate scale table
															  "UPDATE"
															)
								else:
									#build dictionary for condition key
									condKey = getConditionKey(usage,		#Usage of the condition table; constant "E"
															  tableNum,	  	#condition table
															  app,		  	#Application; constant"V"
															  condType, 	#condition type
															  variableKey,  #variable key
															  sOrg,		  	#sales organisation; Constant "1000"
															  distCh,		#disctribution channel; Constant "10"
															  div,				#division; constant "PG"
															  agrNum,		#Agreement Number
															  rebType,	  	#Agreement type
															  refDocNum,	#Reference Document Number
															  recipient,	#Rebate recipient
															  currency,	  	#Currency Key
															  validFrom, #agreement valid from
															  validTo,	#agreement valid to
															  validFrom,	#rebate valid from
															  validTo,		#rebate valid to
															  func, 		#Function; constant "009"
															  appObj, 	  	#Texts: Application Object; constant "KONA"
															  txtId,  	  	#Text ID; constant "ZAGR"
															  langKey, 	  	#Language Key; constant "E"
															  tagCol,		#Tag column; constant "*"
															  txtLine,		#Text line
															  scaleType, 	#Scale Type; constant "A"
															  scaleInd,  	#Scale basis indicator; constant "C"
															  scaleUnit, 	#Condition scale unit of measure
															  calcType,	  	#Calculation type for condition
															  rate,		  	#Rate (condition amount or perc
															  rateUnit,		#Rate unit (currency or percent
															  condPriceUnit,#Condition pricing unit
															  condUnit,		#Condition unit
															  mat,			#Material for rebate settlement; constant "SETTLEMENT MAT"
															  accAmt,		#Accrual Amount
															  scale,		#rebate scale table
															  "UPDATE"
															)
									break
						else:
							#build dictionary for condition key
							condKey = getConditionKey(usage,		#Usage of the condition table; constant "E"
													  tableNum,	  	#condition table
													  app,		  	#Application; constant"V"
													  condType, 	#condition type
													  variableKey,  #variable key
													  sOrg,		  	#sales organisation; Constant "1000"
													  distCh,		#disctribution channel; Constant "10"
													  div,				#division; constant "PG"
													  agrNum,		#Agreement Number
													  rebType,	  	#Agreement type
													  refDocNum,	#Reference Document Number
													  recipient,	#Rebate recipient
													  currency,	  	#Currency Key
													  validFrom, #agreement valid from
													  validTo,	#agreement valid to
													  validFrom,	#rebate valid from
													  validTo,		#rebate valid to
													  func, 		#Function; constant "009"
													  appObj, 	  	#Texts: Application Object; constant "KONA"
													  txtId,  	  	#Text ID; constant "ZAGR"
													  langKey, 	  	#Language Key; constant "E"
													  tagCol,		#Tag column; constant "*"
													  txtLine,		#Text line
													  scaleType, 	#Scale Type; constant "A"
													  scaleInd,  	#Scale basis indicator; constant "C"
													  scaleUnit, 	#Condition scale unit of measure
													  calcType,	  	#Calculation type for condition
													  rate,		  	#Rate (condition amount or perc
													  rateUnit,		#Rate unit (currency or percent
													  condPriceUnit,#Condition pricing unit
													  condUnit,		#Condition unit
													  mat,			#Material for rebate settlement; constant "SETTLEMENT MAT"
													  accAmt,		#Accrual Amount
													  scale,		#rebate scale table
													  "UPDATE"
													)
					else:
						#build dictionary for condition key
						condKey = getConditionKey(usage,		#Usage of the condition table; constant "E"
												  tableNum,	  	#condition table
												  app,		  	#Application; constant"V"
												  condType, 	#condition type
												  variableKey,  #variable key
												  sOrg,		  	#sales organisation; Constant "1000"
												  distCh,		#disctribution channel; Constant "10"
												  div,				#division; constant "PG"
												  agrNum,		#Agreement Number
												  rebType,	  	#Agreement type
												  refDocNum,	#Reference Document Number
												  recipient,	#Rebate recipient
												  currency,	  	#Currency Key
												  validFrom, #agreement valid from
												  validTo,	#agreement valid to
												  validFrom,	#rebate valid from
												  validTo,		#rebate valid to
												  func, 		#Function; constant "009"
												  appObj, 	  	#Texts: Application Object; constant "KONA"
												  txtId,  	  	#Text ID; constant "ZAGR"
												  langKey, 	  	#Language Key; constant "E"
												  tagCol,		#Tag column; constant "*"
												  txtLine,		#Text line
												  scaleType, 	#Scale Type; constant "A"
												  scaleInd,  	#Scale basis indicator; constant "C"
												  scaleUnit, 	#Condition scale unit of measure
												  calcType,	  	#Calculation type for condition
												  rate,		  	#Rate (condition amount or perc
												  rateUnit,		#Rate unit (currency or percent
												  condPriceUnit,#Condition pricing unit
												  condUnit,		#Condition unit
												  mat,			#Material for rebate settlement; constant "SETTLEMENT MAT"
												  accAmt,		#Accrual Amount
												  scale,		#rebate scale table
												  "UPDATE"
												)
					conditionKey.append(condKey)
		# build rebate for adding rebate conditions
		rebateCond = getRebateXml(conditionKey)
		# serialize the data
		updateJson = RestClient.SerializeToJson(rebateCond)
	#-------------------------------------------------------------------------------
		#build dictionary for condition key
		condKey = getConditionKey(usage,		#Usage of the condition table; constant "E"
								  tableNum,	  	#condition table
								  app,		  	#Application; constant"V"
								  condType, 	#condition type
								  variableKey,  #variable key
								  sOrg,		  	#sales organisation; Constant "1000"
								  distCh,		#disctribution channel; Constant "10"
								  div,			#division; constant "PG"
								  agrNum,		#Agreement Number
								  rebType,	  	#Agreement type
								  refDocNum,	#Reference Document Number
								  recipient,	#Rebate recipient
								  currency,	  	#Currency Key
								  validFrom, #agreement valid from
								  validTo,	#agreement valid to
								  validFrom,	#rebate valid from
								  validTo,		#rebate valid to
								  func, 		#Function; constant "009"
								  appObj, 	  	#Texts: Application Object; constant "KONA"
								  txtId,  	  	#Text ID; constant "ZAGR"
								  langKey, 	  	#Language Key; constant "E"
								  tagCol,		#Tag column; constant "*"
								  txtLine,		#Text line
								  scaleType, 	#Scale Type; constant "A"
								  scaleInd,  	#Scale basis indicator; constant "C"
								  scaleUnit, 	#Condition scale unit of measure
								  calcType,	  	#Calculation type for condition
								  rate,		  	#Rate (condition amount or perc
								  rateUnit,		#Rate unit (currency or percent
								  condPriceUnit,#Condition pricing unit
								  condUnit,		#Condition unit
								  mat,			#Material for rebate settlement; constant "SETTLEMENT MAT"
								  accAmt,		#Accrual Amount
								  scale,		#rebate scale table
								  "CREATE"
								)
		# build rebate for creation
		rebateCreate = getRebateXml(condKey)
		# serialize the data
		createJson = RestClient.SerializeToJson(rebateCreate)
	else:
		createJson = updateJson = ""
	return createJson, updateJson
