#!/usr/bin/env python3.7

"""
Description:

    OVERVIEW

    INITIALIZER

    PROPERTIES

    METHODS

"""
# builtins
import os
import pickle
import sys

# packages
import subprocess

# access
from src.core import *
from src.utils import *


class Runner(Exceptionable, Configurable):

    def __init__(self):

        # initialize Configurable super class
        Configurable.__init__(self)

        # initialize Exceptionable super class
        Exceptionable.__init__(self, SetupMode.NEW)

        # init variables for later use
        self.slide_manager = None
        self.fiber_manager = None

    def validate(self):

        samples = self.search(Config.RUN, 'sample')
        models = self.search(Config.RUN, 'models')
        sims = self.search(Config.RUN, '')

        sample_path = os.path.join('samples', str(), 'runs', '{}.json'.format(sys.argv[1]))


    def run(self, configs: dict):
        # constant sample

        # load all json configs into memory
        configs = self.load_configs()

        # slide manager
        slide_manager.add(SetupMode.OLD, Config.SAMPLE, configs['sample'][0])

        # models
        for model_index, model in enumerate(configs['sample']['models']):

            # fiber manager(s)
            fiber_manager.add(SetupMode.OLD, Config.model, configs['models'][model_index])

            # handoff (to Java) -  Build/Mesh/Solve/Save bases; Extract/Save potentials
            self.handoff()

    def smart_run(self):

        print('\nStarting smart run.')

        def load(path: str):
            return pickle.load(open(path, 'rb'))

        path_parts = [self.path(Config.MASTER, 'samples_path'), self.search(Config.MASTER, 'sample')]

        if not os.path.isfile(os.path.join(*path_parts, 'slide_manager.obj')):
            print('Existing slide manager not found. Performing full run.')
            self.full_run()

        else:
            print('Loading existing slide manager.')
            self.slide_manager = load(os.path.join(*path_parts, 'slide_manager.obj'))

            if os.path.isfile(os.path.join(*path_parts, 'fiber_manager.obj')):
                print('Loading existing fiber manager.')
                self.fiber_manager = load(os.path.join(*path_parts, 'fiber_manager.obj'))

            else:
                print('Existing fiber manager not found. Performing fiber run.')
                self.fiber_run()

        self.save_all()

        if self.fiber_manager is not None:
            self.fiber_manager.save_full_coordinates('TEST_JSON_OUTPUT.json')
        else:
            raise Exception('my dude, something went horribly wrong here')

        self.handoff()

    def full_run(self):
        self.slide_run()
        self.fiber_run()

    def slide_run(self):
        print('\nSTART SLIDE MANAGER')
        self.slide_manager = SlideManager(self.configs[Config.MASTER.value],
                                          self.configs[Config.EXCEPTIONS.value],
                                          map_mode=SetupMode.NEW)

        print('BUILD FILE STRUCTURE')
        self.slide_manager.build_file_structure()

        print('POPULATE')
        self.slide_manager.populate()

        print('WRITE')
        self.slide_manager.write(WriteMode.SECTIONWISE2D)

    def fiber_run(self):
        print('\nSTART FIBER MANAGER')
        self.fiber_manager = FiberManager(self.slide_manager,
                                          self.configs[Config.MASTER.value],
                                          self.configs[Config.EXCEPTIONS.value])

        print('FIBER XY COORDINATES')
        self.fiber_manager.fiber_xy_coordinates(plot=True, save=True)

        print('FIBER Z COORDINATES')
        self.fiber_manager.fiber_z_coordinates(self.fiber_manager.xy_coordinates, save=True)

    def handoff(self):
        comsol_path = self.search(Config.ENV, 'comsol_path')
        jdk_path = self.search(Config.ENV, 'jdk_path')
        project_path = self.search(Config.ENV, 'project_path')
        run_path = os.path.join(project_path, 'config', 'user', 'runs', '{}.json'.format(sys.argv[1]))

        core_name = 'ModelWrapper'

        if sys.platform.startswith('darwin') or sys.platform.startswith('linux'):  # macOS and linux

            subprocess.Popen(['{}/bin/comsol'.format(comsol_path), 'server'], close_fds=True)
            os.chdir('src')
            os.system('{}/javac -classpath ../lib/json-20190722.jar:{}/plugins/* model/*.java -d ../bin'.format(jdk_path,
                                                                                                                comsol_path))
            # https://stackoverflow.com/questions/219585/including-all-the-jars-in-a-directory-within-the-java-classpath
            os.system('{}/java/maci64/jre/Contents/Home/bin/java '
                      '-cp .:$(echo {}/plugins/*.jar | tr \' \' \':\'):../lib/json-20190722.jar:../bin model.{} {} {}'.format(comsol_path,
                                                                                                                           comsol_path,
                                                                                                                           core_name,
                                                                                                                           project_path,
                                                                                                                              run_path))
            os.chdir('..')

        else:  # assume to be 'win64'
            subprocess.Popen(['{}\\bin\\win64\\comsolmphserver.exe'.format(comsol_path)], close_fds=True)
            os.chdir('src')
            os.system('""{}\\javac" -cp "..\\lib\\json-20190722.jar";"{}\\plugins\\*" model\\*.java -d ..\\bin"'.format(jdk_path,
                                                                                                                        comsol_path))
            os.system('""{}\\java\\win64\\jre\\bin\\java" -cp "{}\\plugins\\*";"..\\lib\\json-20190722.jar";"..\\bin" model.{} {} {}"'.format(comsol_path,
                                                                                                                                           comsol_path,
                                                                                                                                           core_name,
                                                                                                                                           project_path,
                                                                                                                                           run_path))
            os.chdir('..')

    def save_all(self):

        print('SAVE ALL')
        path_parts = [self.path(Config.MASTER, 'samples_path'), self.search(Config.MASTER, 'sample')]
        self.slide_manager.save(os.path.join(*path_parts, 'slide_manager.obj'))
        self.slide_manager.output_morphology_data()
        self.fiber_manager.save(os.path.join(*path_parts, 'fiber_manager.obj'))





    # def run(self):
    #     self.map = Map(self.configs[Config.MASTER.value],
    #                         self.configs[Config.EXCEPTIONS.value],
    #                         mode=SetupMode.NEW)
    #
    #     # TEST: Trace functionality
    #     # self.trace = Trace([[0,  0, 0],
    #     #                     [2,  0, 0],
    #     #                     [4,  0, 0],
    #     #                     [4,  1, 0],
    #     #                     [4,  2, 0],
    #     #                     [2,  2, 0],
    #     #                     [0,  2, 0],
    #     #                     [0,  1, 0]], self.configs[Config.EXCEPTIONS.value])
    #     # print('output path: {}'.format(self.trace.write(Trace.WriteMode.SECTIONWISE,
    #     #                                                 '/Users/jakecariello/Box/SPARCpy/data/output/test_trace')))
    #
    #     # TEST: exceptions configuration path
    #     # print('exceptions_config_path:\t{}'.format(self.exceptions_config_path))
    #
    #     # TEST: retrieve data from config file
    #     # print(self.search(Config.MASTER, 'test_array', 0, 'test'))
    #
    #     # TEST: throw error
    #     # self.throw(2)
    #
    #     # self.slide = Slide([Fascicle(self.configs[Config.EXCEPTIONS.value],
    #     #                              [self.trace],
    #     #                              self.trace)],
    #     #                    self.trace,
    #     #                    self.configs[Config.MASTER.value],
    #     #                    self.configs[Config.EXCEPTIONS.value])
    #     pass
    #
    # def trace_test(self):
    #
    #     # build path and read image
    #     path = os.path.join('data', 'input', 'misc_traces', 'tracefile2.tif');
    #     img = cv2.imread(path, -1)
    #
    #     # get contours and build corresponding traces
    #     # these are intentionally instance attributes so they can be inspected in the Python Console
    #     self.cnts, self.hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    #     self.traces = [Trace(cnt[:, 0, :], self.configs[Config.EXCEPTIONS.value]) for cnt in self.cnts]
    #
    #     # plot formats
    #     formats = ['r', 'g', 'b']
    #
    #     # original points and centroids
    #     title = 'Figure 0: original traces with calculated centroids'
    #     print(title)
    #     plt.figure(0)
    #     plt.axes().set_aspect('equal', 'datalim')
    #     for i, trace in enumerate(self.traces):
    #         trace.plot(formats[i] + '-')
    #         trace.plot_centroid(formats[i] + '*')
    #     plt.legend([str(i) for i in range(len(self.traces)) for _ in (0, 1)]) # end of this line is to duplicate items
    #     plt.title(title)
    #     plt.show()
    #
    #     # ellipse/circle/original comparison (trace 0)
    #     title = 'Figure 1: fit comparisons (trace 0)'
    #     print(title)
    #     plt.figure(1)
    #     plt.axes().set_aspect('equal', 'datalim')
    #     self.traces[0].plot(formats[0])
    #     self.traces[0].to_circle().plot(formats[1])
    #     self.traces[0].to_ellipse().plot(formats[2])
    #     plt.legend(['original', 'circle', 'ellipse'])
    #     plt.title(title)
    #     plt.show()
    #
    #     # example stats
    #     pairs = [(0, 1), (1, 2), (2, 0)]
    #     print('\nEXAMPLE STATS')
    #     for pair in pairs:
    #         print('PAIR: ({}, {})'.format(*pair))
    #         print('\tcent dist:\t{}'.format(self.traces[pair[0]].centroid_distance(self.traces[pair[1]])))
    #         print('\tmin dist:\t{}'.format(self.traces[pair[0]].min_distance(self.traces[pair[1]])))
    #         print('\tmax dist:\t{}'.format(self.traces[pair[0]].max_distance(self.traces[pair[1]])))
    #         print('\twithin:\t\t{}'.format(self.traces[pair[0]].within(self.traces[pair[1]])))
    #
    #     title = 'Figure 2: Scaled trace'
    #     print(title)
    #     plt.figure(2)
    #     plt.axes().set_aspect('equal', 'datalim')
    #     self.traces[0].plot(formats[0])
    #     self.traces[0].scale(1.2)
    #     self.traces[0].plot(formats[1])
    #     plt.legend(['original', 'scaled'])
    #     plt.title(title)
    #     plt.show()
    #
    # def fascicle_test(self):
    #     # build path and read image
    #     path = os.path.join('data', 'input', 'misc_traces', 'tracefile5.tif')
    #
    #     self.fascicles = Fascicle.inner_to_list(path,
    #                                             self.configs[Config.EXCEPTIONS.value],
    #                                             plot=True,
    #                                             scale=1.06)
    #
    # def reposition_test(self):
    #     # build path and read image
    #     path = os.path.join('data', 'input', 'samples', 'Cadaver54-3', 'NerveMask.tif')
    #
    #     self.img = np.flipud(cv2.imread(path, -1))
    #
    #     # get contours and build corresponding traces
    #     # these are intentionally instance attributes so they can be inspected in the Python Console
    #     self.nerve_cnts, _ = cv2.findContours(self.img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    #     self.nerve = Nerve(Trace(self.nerve_cnts[0][:, 0, :], self.configs[Config.EXCEPTIONS.value]))
    #
    #     self.fascicles = Fascicle.separate_to_list(os.path.join('data', 'input', 'samples',
    #                                                             'Cadaver54-3', 'EndoneuriumMask.tif'),
    #                                                os.path.join('data', 'input', 'samples',
    #                                                             'Cadaver54-3','PerineuriumMask.tif'),
    #                                                self.configs[Config.EXCEPTIONS.value],
    #
    #
    #                                                plot=False)
    #     self.slide = Slide(self.fascicles, self.nerve,
    #                        self.configs[Config.MASTER.value],
    #                        self.configs[Config.EXCEPTIONS.value])
    #
    #     self.slide.reposition_fascicles(self.slide.reshaped_nerve(ReshapeNerveMode.CIRCLE))
    #
    # def reposition_test2(self):
    #     # build path and read image
    #     path = os.path.join('data', 'input', 'samples', 'Pig11-3', 'NerveMask.tif')
    #     self.img = np.flipud(cv2.imread(path, -1))
    #
    #     # get contours and build corresponding traces
    #     # these are intentionally instance attributes so they can be inspected in the Python Console
    #     self.nerve_cnts, _ = cv2.findContours(self.img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    #     self.nerve = Nerve(Trace(self.nerve_cnts[0][:, 0, :], self.configs[Config.EXCEPTIONS.value]))
    #
    #     self.fascicles = Fascicle.inner_to_list(os.path.join('data', 'input', 'samples',
    #                                                          'Pig11-3', 'FascMask.tif'),
    #                                             self.configs[Config.EXCEPTIONS.value],
    #                                             plot=False,
    #                                             scale=1.05)
    #     self.slide = Slide(self.fascicles, self.nerve,
    #                        self.configs[Config.EXCEPTIONS.value],
    #                        will_reposition=True)
    #
    #     # self.slide.reposition_fascicles(self.slide.reshaped_nerve(ReshapeNerveMode.ELLIPSE))
    #     self.slide.reposition_fascicles(self.slide.reshaped_nerve(ReshapeNerveMode.CIRCLE))
