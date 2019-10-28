python MergeCSVFiles.py -f volunteer.csv -f assignments.csv  -o fullAssignment.csv -lk VolunteerAssignment -rk VolunteerAssignment 
python MergeCSVFiles.py -f records.csv -f fullAssignment.csv -o gssbRegistration.csv -lk FamilyID -rk FamilyID 
