import jenkins
import re
import xml.dom.minidom

REGEX = '@auto-demand'

j = jenkins.Jenkins('http://localhost:8080')
jobs = j.get_jobs();

for job in jobs:
    job_name = job['name']
    job_desc = j.get_job_info(job_name)['description']
    if re.match(REGEX, job_desc):
        print 'Deleting %s' % (job_name)
	j.delete_job(job_name)
