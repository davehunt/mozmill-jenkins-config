import os
import xml.dom.minidom

import jenkins

testruns = (
    {'type': 'functional'},
    {'type': 'update',
     'options': ['--no-fallback']},
    {'type': 'l10n'},
    {'type': 'endurance',
     'options': ['--iterations=100', '--entities=10']},
    {'type': 'remote'},
    {'type': 'addons',
     'options': ['--with-untrusted']})

nodes = (
    {'labels': ['windows', '2k', 'x32'],
     'platforms': ['win32'],
     'environment': 'windows'},
    {'labels': ['windows', 'xp', 'x32'],
     'platforms': ['win32'],
     'environment': 'windows'},
    {'labels': ['windows', 'vista', 'x32'],
     'platforms': ['win32'],
     'environment': 'windows'},
    {'labels': ['windows', '7', 'x64'],
     'platforms': ['win32', 'win64'],
     'environment': 'windows'},
    {'labels': ['windows', '7', 'x32'],
     'platforms': ['win32'],
     'environment': 'windows'},
    {'labels': ['mac', '10.6', 'x64'],
     'platforms': ['mac', 'mac64'],
     'environment': 'mac'},
    {'labels': ['ubuntu', '11.10', 'x32'],
     'platforms': ['linux'],
     'environment': 'linux'},
    {'labels': ['ubuntu', '11.10', 'x64'],
     'platforms': ['linux64'],
     'environment': 'linux'})

testrun_command = '%(script)s ./mozmill-automation/testrun_%(type)s.py --port=2424${EXECUTOR_NUMBER} --junit=results.xml --logfile=%(type)s.log --report=http://mozmill-ondemand.blargon7.com/db/ %(options)s .'

def main():
    j = jenkins.Jenkins('http://localhost:8080')
    count = 1
    for testrun in testruns:
        type = testrun.get('type')
        for node in nodes:
            labels = node.get('labels')
            job_name = '-'.join([type, '-'.join(labels)])
            print '%i: %s' % (count, job_name)
            count = count + 1
            template = open(os.path.join('templates', 'testrun_job.xml'))
            platforms = ''.join(['<string>%s</string>' % platform for platform in node.get('platforms')])
            command = testrun_command % {
                'script': './mozmill-env/run.sh',
                'type': type,
                'options': 'options' in testrun and ' '.join(testrun.get('options')) or ''
            }
            build_wrappers = [ ]
            run_xvnc = '<hudson.plugins.xvnc.Xvnc><takeScreenshot>false</takeScreenshot></hudson.plugins.xvnc.Xvnc>'
            if 'linux' in platforms:
                build_wrappers.append(run_xvnc)
            doc = xml.dom.minidom.parseString(template.read() % {
                'labels': '&amp;&amp;'.join(labels),
                'environment': node.get('environment'),
                'platforms': platforms,
                'testrun_command': command,
                'build_wrappers': '<buildWrappers>' + '\n'.join(build_wrappers) + '</buildWrappers>'})
            if j.job_exists(job_name):
                j.reconfig_job(job_name, doc.toxml())
            else:
                j.create_job(job_name, doc.toxml())

if __name__ == '__main__':
    main()
