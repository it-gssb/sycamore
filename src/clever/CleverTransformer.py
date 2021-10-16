'''
Created on Feb 14, 2021

@author: michaelsassin
'''

from abc import ABC
import argparse
import logging
import os
import shutil
import sys

import pandas as pd

# append the path of the parent directory
sys.path.append(".")

from lib import Generators


logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)

class CSVTransformer(ABC):
    '''
    Base class with elementary spreadsheet manipulation functions
    '''

    def __init__(self, params):
        '''
        Constructor
        '''
        
    def findFile(self, directory, fileNamePrefix, postfix = ''):
        found = None
        for file in os.listdir(directory):
            if file.startswith(fileNamePrefix) and file.endswith(postfix):
                found = file
                break
            
        return found
        
    def loadCSVFile(self, path):
        df = pd.read_csv (path)
        return df

    def loadCSVFileSubset(self, path, subset):
        data = pd.read_csv (path, dtype=str)
        df = pd.DataFrame(data, columns = subset)
        return df
    
    def saveCSVFile(self, dataframe, path):
        dataframe.to_csv(path, index = False)
    
    def copyFile(self, source, target):
        shutil.copyfile(source, target)
        
    def removeDuplicates(self, dataframe):
        dataframe.drop_duplicates(inplace=True)
        
    def dropColumn(self, dataframe, columnName):
        dataframe.drop([columnName], axis=1, inplace=True)
        
    def keepRows(self, dataframe, expression):
        return dataframe[expression(dataframe)]
    
    def addColumn(self, dataframe, index : int, name : str, value = ''):
        size = dataframe.count()[0]
        data = [value] * size
        dataframe.insert(index, name, data)
    
    def addColumnExpr(self, dataframe, index : int, name: str, deriveFunction):
        data = []
        for row in dataframe.iterrows():
            value = deriveFunction(row[1])
            data.append(value)
        dataframe.insert(index, name, data)
    
    def changeColumnName(self, dataframe, oldName, newName):
        dataframe.rename(columns = {oldName: newName}, inplace=True)
    

class SIS2SDS(CSVTransformer):
    '''
    Converts Clever files exported from Sycamore into the Clever
    format required by Microsoft Office 365 School cloud service.
    '''

    def __init__(self, sourceDir, targetDir=None):
        '''
        Constructor
        '''
        
        self.sourceDir = sourceDir
        self.targetDir = targetDir
        
    def getLast(self, name : str):
        if name.strip() == '':
            return ''
        
        return name.split(' ', 1)[1].strip()
    
    def getFirst(self, name : str):
        if name.strip() == '':
            return ''
        
        return name.split(' ', 1)[0].strip()

    def getRole(self, relationship : str):
        if not isinstance(relationship, str):
            # Default value
            return 'Parent'

        relationship = relationship.strip()

        if relationship == 'Mother':
            return 'Parent'
        if relationship == 'Father':
            return 'Parent'
        if relationship == 'Parents':
            return 'Parent'
        if relationship == 'Grandmother':
            return 'Relative'

        print('Unknown relationship "%s"' % (relationship))
        return 'Parent'
    
    def transformParentGuardianRelation(self):
        sourceFile = 'students'
        targetFile = 'guardianrelationship'
        
        # defjne subset of columns to be loaded
        columns = ['Student_id', 'Contact_email', 'Contact_relationship']
        
        fileName = self.findFile(self.sourceDir, sourceFile, '.csv')
        source = os.path.join(self.sourceDir, fileName)
        dataframe = self.loadCSVFileSubset(source, columns)
        
        # remove rows without email
        include = lambda df: pd.notna(df.Contact_email)
        dataframe = self.keepRows(dataframe, include)

        # rename existing column
        self.changeColumnName(dataframe, 'Student_id', 'SIS ID')
        self.changeColumnName(dataframe, 'Contact_email', 'Email')

        # Create Role from Contact_relationship
        deriveFirst = lambda row: self.getRole(row.Contact_relationship)
        self.addColumnExpr(dataframe, len(columns), 'Role', deriveFirst)

        self.dropColumn(dataframe, 'Contact_relationship')

        # remove duplicate rows
        self.removeDuplicates(dataframe)

        target = os.path.join(self.targetDir, f'{targetFile}.csv')
        self.saveCSVFile(dataframe, target)
        
    def transformUser(self):
        sourceFile = 'students'
        targetFile = 'user'
        
        # defjne subset of columns to be loaded
        columns = ['Contact_email', 'Contact_name', 'Contact_phone',
                   'Contact_sis_id']
        
        fileName = self.findFile(self.sourceDir, sourceFile, '.csv')
        source = os.path.join(self.sourceDir, fileName)
        dataframe = self.loadCSVFileSubset(source, columns)

        # remove duplicate rows
        self.removeDuplicates(dataframe)

        # remove rows without email
        include = lambda df: pd.notna(df.Contact_email)
        dataframe = self.keepRows(dataframe, include)

        # rename existing column
        self.changeColumnName(dataframe, 'Contact_email', 'Email')
        self.changeColumnName(dataframe, 'Contact_phone', 'Phone')
        self.changeColumnName(dataframe, 'Contact_sis_id', 'SIS ID')
        
        # add missing column and set default value
        deriveFirst = lambda row: self.getFirst(row.Contact_name.strip())
        self.addColumnExpr(dataframe, 2, 'First Name', deriveFirst)
        
        deriveLast = lambda row: self.getLast(row.Contact_name.strip())
        self.addColumnExpr(dataframe, 3, 'Last Name', deriveLast)

        # drop original column used for deriving new columns
        self.dropColumn(dataframe, 'Contact_name')
        
        target = os.path.join(self.targetDir, f'{targetFile}.csv')
        self.saveCSVFile(dataframe, target)
        
    def createStudentEmailAddress(self, row):
        return Generators.createStudentEmailAddress(row.First_name, row.Last_name)

    def createTeacherEmailAddress(self, row):
        return Generators.createTeacherEmailAddress(row.First_name, row.Last_name, row.Teacher_email)
        
    def transformStudents(self):
        sourceFile = 'students'
        
        # defjne subset of columns to be loaded
        columns = ['Student_id', 'School_id', 'Student_number', 'Dob',
                   'Grade', 'State_id', 'Student_email', 'First_name',
                   'Last_name', 'Middle_name', 'Status']
        
        fileName = self.findFile(self.sourceDir, sourceFile, '.csv')
        source = os.path.join(self.sourceDir, fileName)
        dataframe = self.loadCSVFileSubset(source, columns)

        # rename existing column
        self.changeColumnName(dataframe, 'Student_email', 'Secondary_email')
        
        # remove duplicate rows
        self.removeDuplicates(dataframe)
        
        # add missing column and set default value
        derive = lambda row: self.createStudentEmailAddress(row)
        self.addColumnExpr(dataframe, 2, 'Username', derive)
        
        target = os.path.join(self.targetDir, f'{sourceFile}.csv')
        self.saveCSVFile(dataframe, target)
    
    def transformSections(self):
        sourceFile = 'sections'
        
        # defjne subset of columns to be loaded
        columns = ['Section_id', 'School_id', 'Teacher_id', 'Name', 'Term_name',
                   'Term_start', 'Term_end', 'Course_name', 'Subject', 'Period']
        
        fileName = self.findFile(self.sourceDir, sourceFile, '.csv')
        source = os.path.join(self.sourceDir, fileName)
        dataframe = self.loadCSVFileSubset(source, columns)
        
        # add missing column and set default value
        self.addColumn(dataframe, len(columns), 'Status', 'Active')
        
        target = os.path.join(self.targetDir, f'{sourceFile}.csv')
        self.saveCSVFile(dataframe, target)
    
        
    def transformEnrollments(self):
        sourceFile = 'enrollments'
        
        fileName = self.findFile(self.sourceDir, sourceFile, '.csv')
        source = os.path.join(self.sourceDir, fileName)
        target = os.path.join(self.targetDir, f'{sourceFile}.csv')
        self.copyFile(source, target)
        
    def transformTeachers(self):
        sourceFile = 'teachers'
        
        # defjne subset of columns to be loaded
        columns = ['Teacher_id', 'School_id', 'Teacher_email',
                   'Title', 'Last_name', 'First_name']
        
        fileName = self.findFile(self.sourceDir, sourceFile, '.csv')
        source = os.path.join(self.sourceDir, fileName)
        dataframe = self.loadCSVFileSubset(source, columns)
        
        deriveUsername = lambda row: self.createTeacherEmailAddress(row)
        self.addColumnExpr(dataframe, 3, 'Username', deriveUsername)

        deriveEmail = lambda row: self.createTeacherEmailAddress(row)
        self.addColumnExpr(dataframe, 2, 'Teacher_email_new', deriveEmail)
        self.dropColumn(dataframe, 'Teacher_email')
        self.changeColumnName(dataframe, 'Teacher_email_new', 'Teacher_email')
        
        target = os.path.join(self.targetDir, f'{sourceFile}.csv')
        self.saveCSVFile(dataframe, target)
        
    def transformSchool(self):
        sourceFile = 'schools'
        
        # defjne subset of columns to be loaded
        columns = ['School_id', 'School_name', 'Low_grade', 'High_grade',
                   'Principal', 'Principal_email']
        
        fileName = self.findFile(self.sourceDir, sourceFile, '.csv')
        source = os.path.join(self.sourceDir, fileName)
        dataframe = self.loadCSVFileSubset(source, columns)
        
        # add missing column and set default value
        self.addColumn(dataframe, 2, 'School_number', 2132)
        
        self.dropColumn(dataframe, 'Principal_email')
        self.addColumn(dataframe, len(columns), 'Principal_email', 'principal@gssb.org')

        target = os.path.join(self.targetDir, f'{sourceFile}.csv')
        self.saveCSVFile(dataframe, target)
    
        
    def transform(self):
        '''
        Orchestrates CSV file transformation
        '''
        
        self.transformSchool()
        self.transformTeachers()
        self.transformEnrollments()
        self.transformSections()
        self.transformStudents()
        self.transformUser()
        self.transformParentGuardianRelation()

        
        
def parseArguments():
    parser = argparse.ArgumentParser(description='Clever Transformation details')
    parser.add_argument('-s', '--sourceDir', dest='sourceDir', action='store',
                        type=str, required=True,
                        help='source directory with SIS Clever files')
    parser.add_argument('-t', '--targetDir', dest='targetDir', action='store',
                        type=str, default=None,
                        help='target directory with SDS Clever files')

    args = parser.parse_args()
    
    if not args.targetDir:
        args.targetDir = os.path.join(args.sourceDir, '/SDS')
        
    return args

if __name__ == "__main__" :
    args = parseArguments()

    transformer = SIS2SDS(args.sourceDir, args.targetDir)
    transformer.transform()
