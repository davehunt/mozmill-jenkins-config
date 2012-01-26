""" Script to create and trigger Firefox testruns in Jenkins. """

import ConfigParser
import os
import re
import sys
import uuid
import xml.dom.minidom

import jenkins


def main():
    j = jenkins.Jenkins('http://localhost:8080')

    if not len(sys.argv) == 2:
        print 'Configuration file not specified.'
        print 'Usage: %s config' % sys.argv[0]
        sys.exit(1)

    # Read-in configuration options
    config = ConfigParser.SafeConfigParser()
    config.read(sys.argv[1])

    # Check testrun entries
    testrun = { }
    for entry in config.options('testrun'):
        testrun.update({entry: config.get('testrun', entry)})
    testrun = testrun

    # Define job and triggers
    job_name = 'ondemand-%s-%s' % (testrun['script'], uuid.uuid4())
    triggers = [ ]

    # Iterate through all target nodes
    for section in config.sections():
        # Retrieve the platform, i.e. win32 or linux64
        if not config.has_option(section, 'platform'):
            continue
        platform = config.get(section, 'platform')
        node_labels = section.split(' ')
        sub_job_name = '%s-%s' % (testrun['script'], '-'.join(node_labels))

        # Iterate through all builds per platform
        for entry in config.options(section):
            locales = [ ]
            build_type = 'release'

            # Expression to parse versions like: '5.0', '5.0#3', '5.0b1', '5.0b2#1'
            pattern = re.compile(r'(?P<version>[\d\.]+(?:\w\d+)?)(?:#(?P<build>\d+))?')
            try:
                (version, build) = pattern.match(entry).group('version', 'build')
                locales = config.get(section, entry).split(' ')

                # If a build number has been specified we have a candidate build
                build_type = 'candidate' if build else build_type
            except:
                continue

            # Create triggered job for each listed locale
            for locale in locales:
                triggers.append({
                    'job_name': sub_job_name,
                    'parameters': {
                        'PLATFORM': platform,
                        'BUILD_TYPE': build_type,
                        'VERSION': version,
                        'BUILD_NUMBER': build or '1',
                        'LOCALE': locale
                    }
                })

    # Create parameterized build triggers
    pbt_template = open(os.path.join('templates', 'parameterized_build_trigger_config.xml')).read()
    pbts = [ ]
    for trigger in triggers:
        pbts.append(pbt_template % {
            'job_name': trigger['job_name'],
            'parameters': '\n'.join(['%s=%s' % (k, v) for k, v in trigger['parameters'].items()])})

    # Create on-demand-job
    job_template = open(os.path.join('templates', 'on_demand_job.xml')).read()
    job_config = xml.dom.minidom.parseString(job_template % {
        'parameterized_build_trigger_config': '\n'.join(pbts)})
    print 'Creating job: %s' % job_name
    j.create_job(job_name, job_config.toxml())

    # Trigger on-demand job
    print 'Building job: %s' % job_name
    j.build_job(job_name)

if __name__ == "__main__":
    main()
