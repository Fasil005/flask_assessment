import pandas as pd


class BaseFilter:
    """
    This class represents a base class 
    for filter that operates on data read and save Excel file.
    """

    def __init__(self, filename):
        
        self.filename = filename
        self.data = self.read_file()


    def read_file(self,):
        """ Read data from an Excel file """

        data = pd.read_excel(self.filename)
        return data
    

    def save_file(self, filename):
        """ Save the DataFrame to an Excel file """
        self.filename = filename + ".xlsx"
        path = "storage/" + self.filename
        self.data.to_excel(path)

    
    def filter(self, payloads, list_input=False):
        """ Filters the DataFrame based on the given payload and save as new excel file """

        if list_input:
            # Filter the DataFrame based on category and numerical filters
            self.filter_category(payloads[0]['eligibilityJson']['categories'])
            self.filter_numeric(payloads[0]['eligibilityJson']['numerical'])

            # Save the filtered DataFrame to an Excel file
            self.save_file(payloads[0]['eligibilityName'])

        else:
            # Filter the DataFrame based on category and numerical filters
            self.filter_category(payloads['categories'])
            self.filter_numeric(payloads['numerical'])

            # Save the filtered DataFrame to an Excel file
            self.save_file(self.filename)

    def to_response(self, ):

        return {
            "file_name": self.filename,
        }



class EligibilityFilter(BaseFilter):
    """
    This class represents a filter for eligibility
    data based on categories and numerical filters.
    It inherits from the BaseFilter class.
    """


    SINGLE_NUMERIC_OP = {
        '=': lambda df, value: df == value,
        '>': lambda df, value: df > value,
        '>=': lambda df, value: df >= value,
        '<': lambda df, value: df < value,
        '<=': lambda df, value: df <= value
    }

    RANGE_NUMERIC_OP = {
        '< X <': lambda df, lvalue, rvalue: (df > lvalue) & (df < rvalue),
        '<= X <': lambda df, lvalue, rvalue: (df >= lvalue) & (df < rvalue),
        '< X <=': lambda df, lvalue, rvalue: (df > lvalue) & (df <= rvalue),
        '<= X <=': lambda df, lvalue, rvalue: (df >= lvalue) & (df <= rvalue),
        '> X >': lambda df, lvalue, rvalue: (df < lvalue) & (df > rvalue),
        '=> X >': lambda df, lvalue, rvalue: (df <= lvalue) & (df > rvalue),
        '> X >=': lambda df, lvalue, rvalue: (df < lvalue) & (df >= rvalue),
        '>= X >=': lambda df, lvalue, rvalue: (df <= lvalue) & (df >= rvalue)
    }


    def filter_category(self, categories):
        
        for category in categories:
            column = category['variable']
            categories_list = category['categoriesList']
            # Filter the DataFrame based on category values
            self.data = self.data.loc[self.data[column].isin(categories_list)]
            

    def filter_numeric(self, numerics):

        for numeric in numerics:

            column = numeric['variable']
            operator = numeric['operator']
                
            
            
            if filter_func := self.SINGLE_NUMERIC_OP.get(operator):

                value = numeric['value']
                # Filter the DataFrame based on single numeric operator
                self.data = self.data.loc[filter_func(self.data[column], value)]

            elif filter_func := self.find_range_operator(operator):
                
                lvalue = numeric['lValue']
                rvalue = numeric['rValue']
                # Filter the DataFrame based on range numeric operator
                self.data = self.data.loc[filter_func(lvalue=lvalue, df=self.data[column], rvalue=rvalue)]

            else:

                raise Exception('Invalid numeric operator')


    def find_range_operator(self, operator):
        """
        Find and retrieve the appropriate 
        range numeric operator function from 
        the RANGE_NUMERIC_OP dictionary.
        """

        keys = self.RANGE_NUMERIC_OP.keys()

        operator = operator.split(' ')
        for key in keys:
            key_in_list = key.split(' ')
            # Check if the first and last values of the operator and key are the same or reversed
            if ((operator[0] == key_in_list[0] or operator[0][::-1] == key_in_list[0]) and 
                (operator[2] == key_in_list[2] or operator[2][::-1] == key_in_list[2])):
                return self.RANGE_NUMERIC_OP.get(key)
        return None
    
    


class RuleFilter(BaseFilter):

    """
    Filter and process data based on rules and thresholds.
    It inherits from the BaseFilter class.
    """

    NOT_EXIST_VARIABLES = []
    NOT_EXIST_VARIABLES_PAYLOAD = []


    def __init__(self, *args, **kwargs):
        super(RuleFilter, self).__init__(*args, **kwargs)
        self.duplicate_data = self.data.copy()


    def filter_category(self, categories):
        """
        Filter categories and assign subscore values to corresponding rows and columns.
        """
        PAYLOAD_COLUMNS = {"Unnamed: 0",}

        for category in categories:
            column = category['variable']
            description_list = category['description']
            subscore = category['subscore']
            PAYLOAD_COLUMNS.add(column)


            # Check if the column exists in the data
            if column not in self.duplicate_data.columns:
                # Store the column name in the NOT_EXIST_VARIABLES list
                self.NOT_EXIST_VARIABLES.append(column)
            else:
                # Add a new column with None values
                self.duplicate_data[column.lower() + "_score"] = None
                # Assign subscore values to corresponding rows
                for description, subscore_value in zip(description_list, subscore):
                    # breakpoint()
                    row_index = self.duplicate_data[self.duplicate_data[column] == description].index[0]
                    self.duplicate_data.at[row_index, column.lower() + "_score"] = subscore_value
        
        self.NOT_EXIST_VARIABLES_PAYLOAD = list(self.data.columns.difference(PAYLOAD_COLUMNS))

    def filter_numeric(self, numerics):
        """
        Filter numeric values based on 
        the provided thresholds and assign subscore values.
        """
        
        # Iterate over the numeric filters
        for numeric in numerics:

            column = numeric['variable']
            description = numeric['description']
            subscore = numeric['subscore']

            if column not in self.data.columns:
                # Store the column name in the NOT_EXIST_VARIABLES list
                self.NOT_EXIST_VARIABLES.append(column)
            else:
                

                # Iterate over the descriptions and assign subscore values
                for i, desc in enumerate(description):

                    if desc.startswith('<'):
                        # Assign subscore if the value is less than the threshold
                        self.duplicate_data.loc[self.duplicate_data[column]<int(desc[1:]), column.lower() + "_score"] = subscore[i]
                    elif desc.startswith('>'):
                        # Assign subscore if the value is greater than the threshold
                        self.duplicate_data.loc[self.duplicate_data[column]>int(desc[1:]), column.lower() + "_score"] = subscore[i]
                    elif '-' in desc:
                        # Assign subscore if the value is within the range
                        range_values = desc.split('-')
                        self.duplicate_data.loc[(self.duplicate_data[column] >= int(range_values[0])) & 
                                                (self.duplicate_data[column] <= int(range_values[1])), 
                                                column.lower() + "_score"] = subscore[i]
                    else:
                        # Assign None to the subscore column
                        self.duplicate_data.loc[:,column.lower() + "_score"]= None



    def save_file(self, filename):

        # Calculate the 'rule_score' column by summing values from columns ending with '_score'
        self.data['rule_score'] = self.duplicate_data.filter(regex='_score$').sum(axis=1).astype(int).tolist()

        path = f"storage/{filename}.xlsx"
        self.data.to_excel(path)

    def to_response(self,):

        return {
            "missing_in_excel": list(set(self.NOT_EXIST_VARIABLES)),
            "missing_in_payload": self.NOT_EXIST_VARIABLES_PAYLOAD,
            "file_name": self.filename
        }


