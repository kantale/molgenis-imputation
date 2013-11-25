

import os
import uuid 

class Molgenis_compute:
	'''
	Class that utilizes the molgenis-compute framework
	'''

	molgenis_compute_sh = 'molgenis-compute/molgenis-compute-core-0.0.1-SNAPSHOT/molgenis_compute.sh'

	pipeline_dir = {
		'liftover' : 'molgenis-pipelines-master/compute5/Liftover_genome_build_PEDMAP',
		'phase' : 'molgenis-pipelines-master/compute5/Imputation_shapeit_phasing',
		'impute' : 'molgenis-pipelines-master/compute5/Imputation_impute2',
	}

	def __init__(self, pipeline_root_directory, root_directory=None):
		self.job_id = self.get_job_id()
		self.pipeline_root_directory = pipeline_root_directory
		if root_directory:
			self.root_directory = root_directory
		else:
			self.root_directory = os.getcwd()
		self.install_tool_helper = Install_tool_helper()

	def get_job_id(self):
		'''
		Return the current job id. A unique id for the current run. 
		'''

		return str(uuid.uuid4()).split('-')[0] # the first part of a random uuid. http://en.wikipedia.org/wiki/Universally_unique_identifier

	def worksheet_writer(self, worksheet_data):
		'''
		Saves worksheet data in csv format
		'''
		
		return '\n'.join([','.join(x) for x in map(list, zip(*worksheet_data))]) + '\n'

	def worksheet_filenamer(self, job_id):
		'''
		Creates a worksheet filename
		'''
		return 'worksheet_' + job_id + '.csv'

	def worksheet_path_filenamer(self, pipeline_name, job_id):
		'''
		Returns the full path of a worksheet
		'''
		worksheet_path = os.path.join(self.root_directory, self.generated_dir_namer(pipeline_name, job_id)) 
		#Make sure this directory exists
		self.install_tool_helper.mkdir(worksheet_path, ignore_if_exist=True)
		worksheet_filename = self.worksheet_filenamer(job_id)
		return os.path.join(worksheet_path, worksheet_filename)

	def worksheet_saver(self, worksheet_filename, worksheet_data, verbose=True):
		'''
		Saves a worksheet file
		'''		
		print 'Saving worksheet file :%s' % worksheet_filename
		worksheet_file = open(worksheet_filename, 'wb')
		worksheet_file.write(self.worksheet_writer(worksheet_data))
		worksheet_file.close()

	def create_worksheet(self, job_id, pipeline_name, worksheet_data, verbose=True):
		'''
		Creates the worksheet file
		'''
		worksheet_filename_path = self.worksheet_path_filenamer(pipeline_name, job_id)
		self.worksheet_saver(worksheet_filename_path, worksheet_data, verbose)

	def generated_dir_namer(self, pipeline_name, job_id, generated_dir='generated'):
		'''
		Creates a name for the directory of the generated scripts 
		'''
		return os.path.join(generated_dir, pipeline_name) + '_' + job_id
		
	def create_root_worksheet(self, pipeline_name):
		'''
		Saves the information of the root directory for all files and tools in the pipelines
		'''
		root_worksheet = os.path.join(self.root_directory, self.generated_dir_namer(pipeline_name, self.job_id), 'root_' + self.job_id + '.csv')
		with open(root_worksheet, 'w') as root_worksheet_f:
			root_worksheet_f.write('root\n')
			root_worksheet_f.write(self.root_directory)
			
		self.root_worksheet = root_worksheet

	def results_dir_namer(self, pipeline_name, job_id, results_dir='results'):
		'''
		Creates the name of the directory where the results will be stored
		'''
		return os.path.join(self.root_directory, results_dir, pipeline_name  + '_' + job_id)

	def molgenis_command_formatter(self, pipeline_name, job_id, backend):
		'''
		Format the command that generates the scripts
		'''
		command = [
			'sh',
			self.molgenis_compute_sh,
			'--generate',
			'--path', os.path.join(self.pipeline_root_directory, self.pipeline_dir[pipeline_name]),
			'--workflow', 'workflow.csv',
			'--parameters', 'parameters.csv',
			self.worksheet_path_filenamer(pipeline_name, job_id),
			self.root_worksheet,
			'--rundir', self.generated_dir_namer(pipeline_name, job_id),
			'--backend', backend,
			'--database', 'none',
		]

		return command 

	def submit_generated_script(self, pipeline_name, job_id, backend):
		'''
		submit generated scripts for execution
		'''

		generated_dir = self.generated_dir_namer(pipeline_name, job_id)

		print 'Generated %s scripts in: %s' % (backend, generated_dir)
		print 'Submitting..'
		os.chdir(generated_dir)
		self.install_tool_helper.execute('sh submit.sh')
		os.chdir(self.root_directory)
		print 'Finished %s' % pipeline_name 

	def worksheet_generate_submit(self, pipeline_name, worksheet_data, backend, submit=True):
		'''
		Create worksheet, 
		Generate scripts
		Submit generated scripts
		'''

		self.create_worksheet(self.job_id, pipeline_name, worksheet_data, verbose=True)
		self.create_root_worksheet(pipeline_name)
		command = self.molgenis_command_formatter(pipeline_name, self.job_id, backend)

		self.install_tool_helper.execute(' '.join(command))

		if submit:
			self.submit_generated_script(pipeline_name, self.job_id, backend)

		generated_dir = self.generated_dir_namer(pipeline_name, self.job_id)



def Length_of_chromosomes_build_37():
	"""
	>>> print sum([y for x,y in Length_of_chromosomes_build_37().iteritems()])
	3095667412
	"""
	return {
		"1" : 249250621,
		"2" : 243199373,
		"3" : 198022430,
		"4" : 191154276,
		"5" : 180915260,
		"6" : 171115067,
		"7" : 159138663,
		"8" : 146364022,
		"9" : 141213431,
		"10" : 135534747,
		"11" : 134996516,
		"12" : 133851895,
		"13" : 115169878,
		"14" : 107349540,
		"15" : 102531392,
		"16" : 90354753,
		"17" : 81195210,
		"18" : 78077248,
		"19" : 59128983,
		"20" : 63025520,
		"21" : 48129895,
		"22" : 51304566,
		"X" : 155270560,
		"Y" : 59373566,
	}


import os
from subprocess import call

class Install_tool_helper:
	'''
	This is a collection of static methods useful for installing tools in the system
	'''

	@staticmethod
	def which(program):
		'''
		Emulates the behavior of the unix 'which' command
		Code taken and adjusted from here: http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
		'''

		def is_exe(fpath):
			return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

		fpath, fname = os.path.split(program)
		if fpath:
			if is_exe(program):
				return program
		else:
			for path in os.environ["PATH"].split(os.pathsep):
				path = path.strip('"')
				exe_file = os.path.join(path, program)
				if is_exe(exe_file):
					return exe_file

		return None

	@staticmethod
	def get_download_command():
		'''
		Assess which download command from 'wget' and 'curl' are available in the system.
		Returns a function that takes two arguments: A URL and file to save the contents of the URL
		'''

		#Check if wget exists..
		if Install_tool_helper.which('wget'):
			download_command = lambda link, output_file : 'wget -O %s %s' % (output_file, link)
		elif Install_tool_helper.which('curl'):
			#download_command = lambda link, output_file : 'curl %s > %s' % (link, output_file)
			download_command = lambda link, output_file : (Install_tool_helper.execute, ['curl %s' % (link)], {'stdout' : output_file})
		else:
			raise Exception('Error: Could not find any of the wget or curl commands')

		return download_command

	@staticmethod
	def execute(command, stdout=None, stop_if_error=False):
		'''
		This is a generic function for shell commands and function calls 

		If command is str then shell command is assumed

		If command is tuple then function call is assumed. The first element of the tuple
		should be the calling function, the second is a list with parameters and 
		(optionally) the third are keyed arguments 

		if command is a list then this function is executed recursively with the elements
		of the list

		Returns: 0

		'''

		if type(command) is str:
			print 'Running:', command
			stdf = open(stdout, 'wb') if stdout else None
			ret = call(command.split(), stdout=stdf)

			if ret:
				if stop_if_error:
					raise Exception('Problem while running: %s' % command)
				else:
					print 'Warning: Non zero code returned when running: %s' % command

		elif type(command) is tuple:
			if len(command) == 2:
				print command
				command[0](*command[1])
			elif len(command) == 3:
				command[0](*command[1], **command[2])
			else:
				raise Exception('Don\'t know how to run: %s. tuple should have 2 or 3 items' % (str(command))) 
			return 0

		elif type(command) is list:
			for item in command:
				Install_tool_helper.execute(item, stdout=stdout, stop_if_error=stop_if_error)

		else:
			raise Exception('Invalid type for command parameter: %s ' % (type(command).__name__))

		return 0

	@staticmethod
	def mkdir(path, ignore_if_exist=False):
		'''
		Make directory
		if ignore_if_exist is set to True, raise exception if the path exists
		'''

		try:
			os.makedirs(path)
		except OSError as e:
			if 'File exists' in str(e):
				if ignore_if_exist:
					return 1
				else:
					raise e

		return 0

	@staticmethod
	def check_if_file_exists(path, raise_exception=False):
		'''
		Chcek if file exists

		If file does not exist and raise_exception is True then raise an Exception
		'''

		if os.path.isfile(path):
			return True

		if raise_exception:
			raise Exception('File not found: ' + str(path))

		return False

	@staticmethod
	def install_tool(install_actions, target_directory=None, tool_directory=None, tool_filename=None, tool_link=None, current_working_directory=None):
		'''
		Install a tool

		Parameters:
		target_directory : The directory where the installation will take place. This method assumes that this directory exists already. 
		tool_directory : The directory name of the tool. This directory is created under the 'target_directory'
		tool_filename : The name of the file that contains the tool. Usually this is an archive file. This is not the name of the executable,
		                but the name of the file that is donloaded.
		tool_link : The URL that points to the tool
		current_working_directory : The current working directory. This is the directory to 'return' after installing the tool

		The installation happens after following a series of actions. These actions are described as a list of strings in 
		the install_actions parameter. 

		The actions are:
			* cd_target_directory : changes directory to the target_directory
			* cd_tools_directory : changes directory to the tool_directory
			* cd_current_working_directory : changes directory to the current_working_directory
			* mkdir: creates the tool_directory
			* download: downloads the tool_link
			* download_in_directory: downloads the tool_link in the tool_directory
			* untar: untars the tool_filename
			* untar_in_directory: untars the tool_filename in the tool_directory
			* unzip: unzips the tool_filename
			* mv: moves the tool_filename to the tool_directory
			* make_executable_in_directory: Makes executable the tool_filename in the tool_directory
			* make: Runs the make command in the tool_directory
			* check_if_file_exists: Checks if the tool_filename exists

		For example a common configuration is: install_actions = ['cd_target_directory', 'download', 'untar', 'make']

		'''

		commands = []
		for action in install_actions:
			if action == 'cd_target_directory':
				commands += [(os.chdir, [target_directory])]
			elif action == 'cd_tools_directory':
				commands += [(os.chdir, [tool_directory])]
			elif action == 'cd_current_working_directory':
				commands += [(os.chdir, [current_working_directory])]
			elif action == 'mkdir':
				commands += [(Install_tool_helper.mkdir, [tool_directory, True])]
			elif action == 'download':
				commands += [Install_tool_helper.get_download_command()(tool_link, tool_filename)]
			elif action == 'download_in_directory':
				commands += [Install_tool_helper.get_download_command()(tool_link, os.path.join(tool_directory, tool_filename))]
			elif action == 'untar':
				commands += ['tar zxvf %s' % (tool_filename)]
			elif action == 'untar_in_directory':
				commands += ['tar zxvf %s -C %s' % (os.path.join(tool_directory, tool_filename), tool_directory)]
			elif action == 'unzip':
				commands += ['unzip %s' % (tool_filename)]
			elif action == 'mv':
				commands += [(os.rename, [tool_filename, os.path.join(tool_directory, tool_filename)])]
			elif action == 'make_executable_in_directory':
				commands += ['chmod a+x %s' % (os.path.join(tool_directory, tool_filename))]
			elif action == 'make':
				commands += [(os.chdir, [tool_directory])]
				commands += ['make']
				commands += [(os.chdir, ['..'])]
			elif action == 'check_if_file_exists':
				commands += [(Install_tool_helper.check_if_file_exists, [tool_filename, True])]
			else:
				raise Exception('Invalid action: %s' % (str(action)))

		Install_tool_helper.execute(commands)



import re
import os
import glob
import gzip
import sys

try:
	import numpy
except ImportError as e:
	print str(e)
	print '''
	Could not import numpy. Numpy is a prerequisite for this method.
	Please refer to http://www.numpy.org/ for installation instructions,
	or use anaconda: https://store.continuum.io/cshop/anaconda/ 
'''
	sys.exit(1)

import tempfile
import mimetypes

class bioinformatics_file_helper:
	'''
	This is a collection of common functions used commonly
	when opening and processing files with genotype information
	'''

	@staticmethod
	def get_alleles(genotypes):
		'''
		genotypes: a list with tuples of genotypes for the same SNP. i.e: [('A', 'A'), ('A', 'G'), ('G', '0')]
		returns: a tuple with the different alleles. i.e ('A', 'G')
		The alleles in the tuple are sorted according to their frequency.
		'''

		flat_genotypes = [genotype for genotype_pair in genotypes for genotype in genotype_pair]
		all_alleles = list(set(flat_genotypes) - set(['0']))
		all_alleles_c = len(all_alleles)

		if all_alleles_c == 0:
			return ('0', '0')
		if all_alleles_c == 1:
			return (all_alleles[0], '0')
		else:
			count_sorted = {x : flat_genotypes.count(x) for x in all_alleles}
			return sorted(count_sorted, key=lambda x : count_sorted[x])[::-1] #Sort and revert

	@staticmethod
	def get_chromosome_files(path, chromosome_exp=r'chr%(chromosome)s'):
		'''
		Check if there are files that match 'chromosome_exp'
		Check for multiple matches. 
		This method is useful for getting genomic files split per chromosome

		Return: A pattern that match the files and the chromosomes that matched. For example if the files are:
		path/data_chr1.vcf
		path/data_chr2.vcf

		The return value of get_chromosome_files('path/*.vcf') will be:

		('path/data_chr%(chromosome)s.vcf', [1,2])
		'''

		reference_files = glob.glob(path)
		if not reference_files:
			print 'Warning: path %s is empty' % path
			return None, None
		reference_filenames = [os.path.split(x)[1] for x in reference_files]

		if '%(chromosome)s' not in chromosome_exp:
			print "Warning: Could not find chromosome identifier '%(chromosome)s' in parameter chromosome_exp"
			return None, None

		chr_reg_expr = chromosome_exp.replace('%(chromosome)s', '([\d]+|X|Y)')

		#Check if there is a chromosome identifier in the filenames
		stem_d = {}
		chromosomes = []
		for reference_filename in reference_filenames:
			s = re.search(chr_reg_expr, reference_filename)
			if s:
				chromosome = s.group(1)
				if chromosome in [str(x) for x in range(1,23)] + ['X', 'Y']:
					stem = reference_filename.replace(s.group(0), chromosome_exp)
					if stem_d.has_key(chromosome):
						print 'Warning: Do not know which of these two files is the proper file for chromosome %s: %s, %s' % (chromosome, stem_d[chromosome] % {'chromosome' : chromosome}, reference_filename)
						return None, None
					else:
						stem_d[chromosome] = stem
						chromosomes += [chromosome]
				else:
					print 'Warning: Ignoring file: %s . Cannot recognize chromosome: %s' % (reference_filename, chromosome)
		#Check if all stems are the same:
		stem_set = set([values for values in stem_d.itervalues()])
		if len(stem_set) > 1:
			print 'Warning: the \'%s\' part should be in the same position for all the files' % (chromosome_exp)
			print 'These are not the same:'
			print '\n'.join(stem_set)
			return None, None
		if len(stem_set) == 0:
 			print 'Warning: could not find %s in any file in path %s' % (chromosome_exp, path)
			return None, None

		return list(stem_set)[0], chromosomes

	@staticmethod
	def line_reader(f):
		'''
		f: an opened file 
		Returns a list of identifiers in a line that is whitespace separated
		'''

		return f.readline().replace('\n', '').split()

	@staticmethod
	def line_writer(f, line, sep='\t'):
		'''
		f: a file
		line: a list of values

		Saves the list 'line' in file 'f' separated with 'sep'
		'''
		return f.write(sep.join(line) + '\n')

	@staticmethod
	def open_file_read(filename):
		'''
		Checks the type of filename and returns a file or a string stream
		'''
		if type(filename) is str:
			#Check if file is a gzip
			if mimetypes.guess_type(filename)[1] == 'gzip':
				return gzip.open(filename,'rb')

			return open(filename, 'rU')
		else:
			filename.seek(0)
			return filename

	@staticmethod
	def open_file_write(filename):
		'''
		Checks the type of filename and returns a file or a string stream
		'''
		if type(filename) is str:

			if mimetypes.guess_type(filename)[1] == 'gzip':
				return gzip.open(filename, 'wb')

			return open(filename, 'w')
		else:
			return filename

	@staticmethod
	def close_file(stream):
		'''
		Checks the type of filesource and closes the file
		'''
		if type(stream) is file:
			stream.close()

	@staticmethod
	def line_generator(filename):
		'''
		filename: a filename or open file
		Generates lines from a filename. Lines are splitted on whitespaces
		'''

		read_from = bioinformatics_file_helper.open_file_read(filename)

		line_counter = 0
		for l in read_from:
			line_counter += 1
			s = l.replace('\n', '').split()
			yield line_counter, s

		bioinformatics_file_helper.close_file(read_from)

	@staticmethod
	def column_generator(filename, batch_size=10000):
		'''
		filename: a filename or open file
		Reads a column of a file.
		After 'batch_size' reads reopens the file
		yields a tuple: current column, line
		'''

		start_column = 0
		line_counter = 0
		while True:
			to_return = []
			finished = False

			f = bioinformatics_file_helper.open_file_read(filename)
			for l in f:
				s = l.replace('\n', '').split()
				#Store a batch_size at most records
				current_line_batch = s[start_column: start_column + batch_size]
				
				if not len(current_line_batch):
					finished = True
					break

				to_return += [current_line_batch]

			if finished:
				break

			bioinformatics_file_helper.close_file(f)

			#Transpose
			to_return_transposed = numpy.transpose(to_return)

			#Yield columns
			for line in to_return_transposed:
				line_counter += 1
				yield line_counter, list(line)

			start_column += batch_size

	@staticmethod
	def column_writer(filename, batch_size=10000, silent=False):
		'''
		Saves to file column by column.
		It is implemented as a generator
		If this method consumes too much memory, try lowering the batch_size    
		To suppress output set silent=True

		Example:
		g = write_file_vertical('test.txt')
		g.next()
		g.send(['1', '2'])
		g.send(['3', '4'])
		g.send(['5', '6'])
		g.send(None)
		'''

		old_temp_filename = None
		finished = False
		while not finished:
			current_batch = []
			for current_record in range(batch_size):
				data = (yield True)
				if not data:
					finished = True
					break
				current_batch += [data]

			if current_batch:
				current_batch_transposed = numpy.transpose(current_batch)

				new_temp_file = tempfile.NamedTemporaryFile(delete=False)
				if not silent:
					print 'Created: ', new_temp_file.name

				if old_temp_filename:
					old_temp_generator = line_generator(old_temp_filename)
					for line in current_batch_transposed:
						line_writer(new_temp_file, old_temp_generator.next()[1] + list(line))

					#Close old_temp_file
					for line in old_temp_generator:
						pass

					#delete old_temp_file anymore
					os.unlink(old_temp_filename)
					if not silent:
						print 'Deleted: ', old_temp_filename
				else:
					for line in current_batch_transposed:
						bioinformatics_file_helper.line_writer(new_temp_file, line)

				old_temp_filename = new_temp_file.name
				new_temp_file.close()

		if type(filename) is str:
			os.rename(old_temp_filename, filename)
			if not silent:
				print 'Moved %s to %s' % (old_temp_filename, filename)
		else:
			#Dump temporary file to stream. Then delete it
			temp_file = bioinformatics_file_helper.open_file_read(old_temp_filename)
			for l in temp_file:
				filename.write(l)
			bioinformatics_file_helper.close_file(old_temp_filename)
			os.unlink(old_temp_filename)
			if not silent:
				print 'Delete: ', old_temp_filename
		yield False



import os

class Imputation:
	'''
	This class manages scripts that perform genetic imputation
	It uses Molgenis_compute to handle imputation scripts 
	'''

	#Necessary files and tools for imputation.
	prereq = {
		'link': 'http://molgenis26.target.rug.nl/downloads/molgenis-impute-files.tgz',
		'file': 'molgenis-impute-files.tgz',
		'dir' : None, 
		'install_actions': ['download', 'untar']
		}

	pipelines = {
		'link' : 'https://github.com/kantale/molgenis-pipelines/archive/master.zip',
		'file' : 'molgenis-pipelines.zip',
		'dir' : 'molgenis-pipelines-master',
		'install_actions' : ['cd_target_directory', 'download', 'unzip', 'cd_current_working_directory'],
	}

	shapeit = {
		'link': 'http://www.shapeit.fr/script/get.php?id=18',
		'file': 'shapeit.v2.r644.linux.x86_64.tgz',
		'dir' : 'Shapeit-v2.644',
		'install_actions': ['cd_target_directory', 'mkdir', 'download_in_directory', 'untar_in_directory', 'cd_current_working_directory'],
		}
	
	impute2 = {
		'link': 'http://mathgen.stats.ox.ac.uk/impute/impute_v2.3.0_x86_64_static.tgz',
		'file': 'impute_v2.3.0_x86_64_static.tgz',
		'dir' : 'impute_v2.3.0_x86_64_static',
		'install_actions': ['cd_target_directory', 'download', 'untar', 'mv', 'cd_current_working_directory'],
		}

	liftover = {
		'link': 'http://hgdownload.cse.ucsc.edu/admin/exe/linux.x86_64/liftOver',
		'file': 'liftOver',
		'dir' : 'liftOverUcsc-20120905',
		'install_actions': ['cd_target_directory', 'mkdir', 'download_in_directory', 'make_executable_in_directory', 'cd_current_working_directory'],
		}

	plink = {
		'link': 'http://pngu.mgh.harvard.edu/~purcell/plink/dist/plink-1.07-x86_64.zip',
		'file': 'plink-1.07-x86_64.zip',
		'dir' : 'plink-1.07-x86_64',
		'install_actions': ['cd_target_directory', 'download', 'unzip', 'mv', 'cd_current_working_directory']
		}

	vcftools = {
		'link': 'http://downloads.sourceforge.net/project/vcftools/vcftools_0.1.11.tar.gz?r=http%3A%2F%2Fsourceforge.net%2Fprojects%2Fvcftools%2Ffiles%2F&ts=1374814925&use_mirror=heanet',
		'file': 'vcftools_0.1.11.tar.gz',
		'dir' : 'vcftools_0.1.11',
		'install_actions': ['cd_target_directory', 'download', 'untar', 'make', 'mv', 'cd_current_working_directory']
		}

	genotypeAligner = {
		'link': 'http://www.molgenis.org/jenkins/job/systemsgenetics/nl.systemsgenetics%24genotype-aligner/lastBuild/artifact/nl.systemsgenetics/genotype-aligner/1.1.0/genotype-aligner-1.1.1-jar-with-dependencies.jar',
		'file': 'GenotypeAligner.jar',
		'dir' : 'genotype_aligner/GenotypeAligner-1.1.1',
		'install_actions': ['cd_target_directory', 'cd_tools_directory', 'check_if_file_exists', 'cd_current_working_directory']
		}

	#Reference panels
	reference_panels = {
		'GIANT.phase1_release_v3.20101123' : {
			'description' : 
'''
	Reduced GIANT all population panel (monomorphic and singleton sites, 1092 individuals)

	Dataset description taken from: http://genome.sph.umich.edu/wiki/Minimac:_1000_Genomes_Imputation_Cookbook
	Link: ftp://share.sph.umich.edu/1000genomes/fullProject/2012.03.14/GIANT.phase1_release_v3.20101123.snps_indels_svs.genotypes.refpanel.ALL.vcf.gz.tgz
''',
		'link': 'ftp://share.sph.umich.edu/1000genomes/fullProject/2012.03.14/GIANT.phase1_release_v3.20101123.snps_indels_svs.genotypes.refpanel.ALL.vcf.gz.tgz',
		'file': 'GIANT.phase1_release_v3.20101123.snps_indels_svs.genotypes.refpanel.ALL.vcf.gz.tgz',
		'vcfgz': 'chr%(chromosome)s.phase1_release_v3.20101123.snps_indels_svs.genotypes.refpanel.ALL.vcf.gz',
		'hapsgz': 'chr%(chromosome)s.phase1_release_v3.20101123.snps_indels_svs.genotypes.refpanel.ALL.haps.gz',
		'legendgz': 'chr%(chromosome)s.phase1_release_v3.20101123.snps_indels_svs.genotypes.refpanel.ALL.legend.gz',
		'install_actions': ['cd_target_directory', 'mkdir', 'download_in_directory', 'untar_in_directory', 'cd_current_working_directory'],
		},
		'GIANT.metabo.phase1_release_v3.20101123' : {
			'description' :
'''
	Metabochip (http://www.plosgenetics.org/article/info%3Adoi%2F10.1371%2Fjournal.pgen.1002793) specific reference panel. 
	This reduced reference panel is a time saver, since it focuses on the well-imputable fine-mapping regions.
 
	Dataset description taken from: http://genome.sph.umich.edu/wiki/Minimac:_1000_Genomes_Imputation_Cookbook 
	Link: ftp://share.sph.umich.edu/1000genomes/fullProject/2012.03.14/GIANT.metabo.phase1_release_v3.20101123.snps_indels_svs.genotypes.refpanel.ALL.vcf.gz.tgz
''',
		'link': 'ftp://share.sph.umich.edu/1000genomes/fullProject/2012.03.14/GIANT.metabo.phase1_release_v3.20101123.snps_indels_svs.genotypes.refpanel.ALL.vcf.gz.tgz',
		'dir' : 'GIANT.metabo.phase1_release_v3.20101123',
		'file': 'GIANT.metabo.phase1_release_v3.20101123.snps_indels_svs.genotypes.refpanel.ALL.vcf.gz.tgz',
		'vcfgz': 'chr%(chromosome)s.metabo.phase1_release_v3.20101123.snps_indels_svs.genotypes.refpanel.ALL.vcf.gz',
		'hapsgz': 'chr%(chromosome)s.metabo.phase1_release_v3.20101123.snps_indels_svs.genotypes.refpanel.ALL.haps.gz',
		'legendgz': 'chr%(chromosome)s.metabo.phase1_release_v3.20101123.snps_indels_svs.genotypes.refpanel.ALL.legend.gz',
		'install_actions': ['cd_target_directory', 'mkdir', 'download_in_directory', 'untar_in_directory', 'cd_current_working_directory'],
		},
		}

	genetic_map = 'resources/genetic_map/genetic_map_chr%(chromosome)s_combined_b37.txt'
	hg18tohg19_chain = 'resources/liftover/hg18ToHg19.over.chain'
	reference_dir = 'resources/imputationReference'
	tools_directory = 'tools'

	def __init__(self, tools_dir=None, reference_dir=None, verbose=True):
		'''
		Set up Imputation class
		'''
		self.verbose = verbose
		self.bfh = bioinformatics_file_helper()
		self.cwd = os.getcwd()
		self.install_tool_helper = Install_tool_helper()

		if reference_dir:
			self.reference_dir = reference_dir
		else:
			self.reference_dir = os.path.join(self.cwd, self.reference_dir)

		if tools_dir:
			self.tools_directory = tools_dir
		else:
			self.tools_directory = os.path.join(self.cwd, self.tools_directory)

	def install_imputation_tools(self):
		'''
		Download and install all necessary tools and data for imputation
		'''
		
		#Make dir
		self.install_tool_helper.mkdir(self.tools_directory, ignore_if_exist=True)

		#Check if necessary tools exist
		for tool in ['tar', 'unzip', 'g++', 'java']:
			if not self.install_tool_helper.which(tool):
				raise Exception('Could not find tool: %s . Install and retry' % tool)

		#Download necessary files
		for tool in [self.prereq, self.pipelines, self.shapeit, self.impute2, self.liftover, self.plink, self.vcftools, self.genotypeAligner]:
			self.install_tool_helper.install_tool(
				tool['install_actions'], 
				target_directory=self.tools_directory, 
				tool_directory=tool['dir'], 
				tool_filename=tool['file'], 
				tool_link=tool['link'], 
				current_working_directory=self.cwd,
				)

	def install_reference_panel(self, reference_panel):
		'''
		Install a reference panel
		The details of the reference panel should exist in the member dictionary: reference_panels
		'''

		if self.reference_panels.has_key(reference_panel):
			self.install_tool_helper.install_tool(
				self.reference_panels[reference_panel]['install_actions'],
				target_directory=self.reference_dir,
				tool_directory=self.reference_panels[reference_panel]['dir'],
				tool_filename=self.reference_panels[reference_panel]['file'],
				tool_link=self.reference_panels[reference_panel]['link'],
				current_working_directory = self.cwd,
				)
		else:
			raise Exception('Uknown reference panel: %s' % (reference_panel))

		#Check that everything is ok
		self.check_reference_panel_installation(reference_panel)

	def convert_vcf_to_IMPUTE2(self, reference_panel, chromosome):
		'''
		Convert a reference panel from VCF to IMPUTE2's hap and legend format
		vcftools is used as a convertion tool
		'''
	
		vcfgz_fn = os.path.join(self.reference_dir, reference_panel, self.reference_panels[reference_panel]['vcfgz'])
		total_commands = []
	
		command = []
		command += [os.path.join(self.tools_directory, self.vcftools['dir'], 'bin', 'vcftools')]
		command += ['--gzvcf']
		command += [vcfgz_fn]
		command += ['--IMPUTE']
		command += ['--out']
		command += [vcfgz_fn + '.pyp']
		
		total_commands += [' '.join(command) % {'chromosome' : chromosome}]
		
		#Zip output hap file
		command = ' '.join(['gzip', vcfgz_fn + '.pyp.impute.hap'])
		total_commands += [command % {'chromosome' : chromosome}]
		
		#Zip output legend file
		command = ' '.join(['gzip', vcfgz_fn + '.pyp.impute.legend'])
		total_commands += [command % {'chromosome' : chromosome}]
		
		#mv hap files
		command = ' '.join(['mv', vcfgz_fn + '.pyp.impute.hap.gz',  vcfgz_fn.replace('vcf.gz', 'haps.gz')])
		total_commands += [command % {'chromosome' : chromosome}]
		
		#mv legend files
		command = ' '.join(['mv', vcfgz_fn + '.pyp.impute.legend.gz', vcfgz_fn.replace('vcf.gz', 'legend.gz')])
		total_commands += [command % {'chromosome' : chromosome}]

		#Execute commands
		self.install_tool_helper.execute(total_commands)

	def check_reference_panel_installation(self, reference_panel):
		'''
		Make sure that the reference panel is installed properly 
		and all the files have been inserted in the self.reference_panels dictionary
		'''

		#Check VCF files
		if not self.reference_panels[reference_panel].has_key('vcfgz'):
			raise Exception('Member dictionary reference_panels does not have key: \'vcfgz\'')

		if '%(chromosome)s' not in self.reference_panels[reference_panel]['vcfgz']:
			raise Exception(self.reference_panels[reference_panel]['vcfgz'] + ' does not have a \'%(chromosome)s\' part')


		this_reference_dir = os.path.join(self.reference_dir, self.reference_panels[reference_panel]['dir'])
		info = self.bfh.get_chromosome_files(os.path.join(this_reference_dir, self.reference_panels[reference_panel]['vcfgz'].replace('%(chromosome)s', '*')))
		if not info:
			raise Exception('Reference panel %s had not been installed properly' % reference_panel)

		vcf_pattern, chromosomes = info

		#Check if haps and legend files exist
		if \
			not self.reference_panels[reference_panel].has_key('hapsgz') or \
			not self.reference_panels[reference_panel].has_key('legendgz') or \
			'%(chromosome)s' not in self.reference_panels[reference_panel]['hapsgz'] or \
			'%(chromosome)s' not in self.reference_panels[reference_panel]['legendgz']:

			chrosomes_to_convert = chromosomes[:]
			self.reference_panels[reference_panel]['hapsgz'] = self.reference_panels[reference_panel]['vcfgz'].replace('vcf.gz', 'haps.gz')
			self.reference_panels[reference_panel]['legendgz'] = self.reference_panels[reference_panel]['vcfgz'].replace('vcf.gz', 'legend.gz')
		else:
			chromosomes_to_convert = []
			for chromosome in chromosomes:
				if \
				not os.path.isfile(os.path.join(this_reference_dir, self.reference_panels[reference_panel]['hapsgz']   % {'chromosome' : chromosome})) or \
				not os.path.isfile(os.path.join(this_reference_dir, self.reference_panels[reference_panel]['legendgz'] % {'chromosome' : chromosome})):
					chromosomes_to_convert += [chromosome]

		#Create missing haps and legends files
		for chromosome in chromosomes_to_convert:
			print 'Converting: %s to hap and legend' % self.reference_panels[reference_panel]['vcfgz'] % {'chromosome' : chromosome}
			self.convert_vcf_to_IMPUTE2(reference_panel, chromosome)

	def add_custom_reference_panels(self):
		'''
		Searches for reference panels that are not in the reference_panels dictionary.
		If any found, it is added
		'''

		for dir_entry in glob.glob(os.path.join(self.reference_dir, '*')):
			if os.path.isdir(dir_entry):
				reference_name = os.path.split(dir_entry)[1]
				if not self.reference_panels.has_key(reference_name):
					#Try to add this to the reference panels
					print 'Adding custom reference: ' + reference_name
					self.reference_panels[reference_name] = {'description' : 'Custon panel add from %s' % self.reference_dir}

					stem = self.bfh.get_chromosome_files(os.path.join(dir_entry, '*.vcf.gz'))
					if stem:
						self.reference_panels[reference_name]['vcfgz'] = stem[0]
						self.reference_panels[reference_name]['hapsgz'] = stem[0].replace('vcf.gz', 'haps.gz')
						self.reference_panels[reference_name]['legendgz'] = stem[0].replace('vcf.gz', 'legend.gz')
						self.reference_panels[reference_name]['dir'] = reference_name
						self.check_reference_panel_installation(reference_name)
					else:
						print 'Warning: Could not find *.vcf.gz files in %s' % (self.reference_dir) 

	def list_reference_panels(self):
		'''
		Lists all available reference panels
		'''

		for reference_panel in self.reference_panels:
			print 'name: ', reference_panel
			print 'descritpion: '
			print self.reference_panels[reference_panel]['description']
			print '*' * 30

	def chr_pos_generator(self, chromosomes, position_interval = 5000000):
		'''
		Generates th chr position intervals for the imputation job
		'''

		chromosome_lengths = Length_of_chromosomes_build_37()
		for chromosome in chromosomes:
			length = chromosome_lengths[chromosome]
			for from_pos in range(1, length, position_interval):
				yield (chromosome, from_pos, from_pos + position_interval - 1)

	def perform_liftover(self, study, results, backend='local', submit=True):
		'''
		Generates and submits the liftover scripts
		'''

		mc = Molgenis_compute(self.tools_directory)

		stem_ped = self.bfh.get_chromosome_files(os.path.join(study, '*.ped'))
		if not stem_ped:
			raise Exception('Could not find any file named chr<1-22>.ped in %s' % study)

	
		stem_map = self.bfh.get_chromosome_files(os.path.join(study, '*.map'))
		if not stem_map:
			raise Exception('Could not find any file names chr<1-22>.map in %s' % study)		

		chromosomes = stem_ped[1]

		worksheet_data = [
			['study'] + [mc.job_id for chromosome in chromosomes],
			['studyInputDir'] + [study for chromosome in chromosomes],
			['liftOverChainFile'] + [os.path.join(self.cwd, self.hg18tohg19_chain) for chromosome in chromosomes],
			['outputFolder'] + [results for chromosome in chromosomes],
			['chr'] + chromosomes,
		]

		mc.worksheet_generate_submit('liftover', worksheet_data, backend, submit)

	def perform_phase(self, study, results, studyDataType='BED', additional_shapeit_parameters=' ', backend='local', submit=True):
		'''
		Generates and submits the phasing scripts
		studyDataType can take the following values: 
			BED : for binary plink files
			PED : for text plink files
		'''

		mc = Molgenis_compute(self.tools_directory)
		
		if studyDataType == 'BED':
				pedmap_pattern, chromosomes = self.bfh.get_chromosome_files(os.path.join(study, '*.bed'))
				extensions = ['bed', 'bim', 'fam']
		elif studyDataType == 'PED':
				pedmap_pattern, chromosomes = self.bfh.get_chromosome_files(os.path.join(study, '*.ped'))
				extensions = ['ped', 'map']
		else:
			raise Exception('Unknown value for parameter studyDataType: ' + str(studyDataType))

		if not chromosomes:
			raise Exception('Could not find any files named chr<CHROMOSOME>.%s in study dir: %s' % (studyDataType.lower(), study))

		worksheet_data = [
			['project'] + [mc.job_id for x in chromosomes],
			['m'] + [os.path.join(self.cwd, self.genetic_map % {'chromosome' : chromosome}) for chromosome in chromosomes],
			['outputFolder'] + [results for chromosome in chromosomes],
			['chr'] + chromosomes,
			['additonalShapeitParam'] + [additional_shapeit_parameters for x in chromosomes],
			['studyData'] + [ ' '.join([os.path.join(study, 'chr' + chromosome + '.' + x) for x in extensions])  for chromosome in chromosomes],
			['studyDataType'] + [studyDataType for chromosome in chromosomes],
		]

		mc.worksheet_generate_submit('phase', worksheet_data, backend, submit)

	def perform_impute(self, study, results, reference, additional_impute2_parameters=' ', 
		sample_batch_size=500, 
		position_batch_size=5000000,
		custom_chromosomes=None,
		backend='local', 
		submit=True):
		'''
		Generates and submits the imputation scripts
		'''
		
		def get_sample_chunks(n):
			'''
			Create a list with (from, to) pairs. For sample chunking
			'''
			if sample_batch_size >= n:
				return [[1, n]]

			ratio = n / (n/sample_batch_size)

			ret = []
			for r in range(1, n, ratio):
				if  n-r-ratio+1 < ratio:
					ret += [[r, n]]
					break
				else:
					ret += [[r, r+ratio-1]]

			return ret

		if not reference:
			raise Exception('Invalid reference value: ' + str(reference))

		if not self.reference_panels.has_key(reference):
			self.list_reference_panels()
			raise Exception('Unknown reference panel: ' + reference)

		mc = Molgenis_compute(self.tools_directory)
		reference_dir = os.path.join(self.reference_dir, self.reference_panels[reference]['dir'] )

		haps_pattern, chromosomes = self.bfh.get_chromosome_files(os.path.join(study, '*.haps'))
		if not chromosomes:
			raise Exception('Could not find any files named chr<1-22>.haps in %s' % study)

		#Check for custom chromosomes
		if custom_chromosomes:
			custom_chromosomes = custom_chromosomes.split(',')
			for custom_chromosome in custom_chromosomes:
				if custom_chromosome not in chromosomes:
					raise Exception('Cannot locate reference panel for requested chromosome: %s' % (str(custom_chromosome))
			chromosomes = custom_chromosomes

		#Get number of samples
		with open(os.path.join(study, haps_pattern % {'chromosome': str(chromosomes[0])})) as haps_pattern_f:
			n_samples = (len(haps_pattern_f.readline().split())-5)/2

		sample_chunks = get_sample_chunks(n_samples)
		sample_chunks_n = len(sample_chunks)

		positions = [position for position in self.chr_pos_generator(chromosomes, position_interval=position_batch_size)]

		worksheet_data = [
			['project'] + [mc.job_id for p in positions for sample_chunk in sample_chunks],
			['knownHapsG'] + [os.path.join(study, 'chr%s.haps' % p[0]) for p in positions for sample_chunk in sample_chunks],
			['m'] + [os.path.join(self.cwd, self.genetic_map % {'chromosome' : p[0]}) for p in positions for sample_chunk in sample_chunks],
			['h'] + [os.path.join(reference_dir, self.reference_panels[reference]['hapsgz'] % {'chromosome'  : p[0]}) for p in positions for sample_chunk in sample_chunks],
			['l'] + [os.path.join(reference_dir, self.reference_panels[reference]['legendgz'] % {'chromosome' : p[0]}) for p in positions for sample_chunk in sample_chunks],
			['vcf'] + [os.path.join(reference_dir, self.reference_panels[reference]['vcfgz'] % {'chromosome' : p[0]}).replace('.vcf.gz', '') for p in positions for sample_chunk in sample_chunks],
			['additonalImpute2Param'] + [additional_impute2_parameters for p in positions for sample_chunk in sample_chunks],
			['outputFolder'] + [results for p in positions for sample_chunk in sample_chunks],
			['chr'] + [p[0] for p in positions for sample_chunk in sample_chunks],
			['fromChrPos'] + [str(p[1]) for p in positions for sample_chunk in sample_chunks],
			['toChrPos'] + [str(p[2]) for p in positions for sample_chunk in sample_chunks],
			['fromSample'] + [str(sample_chunk[0]) for p in positions for sample_chunk in sample_chunks],
			['toSample'] + [str(sample_chunk[1]) for p in positions for sample_chunk in sample_chunks],
			['samplechunksn'] + [str(sample_chunks_n) for p in positions for sample_chunk in sample_chunks], 
		]
		mc.worksheet_generate_submit('impute', worksheet_data, backend, submit)

	def perform_action(action, reference, study, results, backend):
		'''
		Action dispatcher
		'''

		if action == 'liftover':
			self.perform_liftover(study, results, backend)
		elif action == 'phase':
			self.perform_phase(study, results, backend)
		elif action == 'impute':
			self.perform_impute(study, results, reference, backend)
		else:
			raise Exception('Unknown action: %s' % str(action))

#Imputation()