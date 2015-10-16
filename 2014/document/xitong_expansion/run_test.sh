#!/bin/sh
#$ -l standby=1
#$ -l m_mem_free=5G,h_rt=4:00:00
# -m eas
# -M lukuang@udel.edu
#$ -t 1-59
vpkg_require python
source /home/1546/myEV/bin/activate
# When a single command in the array job is sent to a compute node,
# its task number is stored in the variable SGE_TASK_ID,
# so we can use the value of that variable to get the results we want:
echo  $model $qid  $mu $SGE_TASK_ID
python json_find.py para  $model $qid  $mu $SGE_TASK_ID
#echo $SGE_TASK_ID
