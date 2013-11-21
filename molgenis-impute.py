
"""
molgenis-impute v.0.7.0
Alexandros Kanterakis, alexandros.kanterakis@gmail.com

Please read documentation in README.md 

"""

import argparse
from imputation import Imputation

if __name__ == '__main__':

	description = """
		MOLGENIS-compute imputation version 0.7.0
	"""

	parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)

	parser.add_argument('--tools_dir', help='Installation directory for imputation tools. Default: <currrent working dir>/tools')
	parser.add_argument('--reference_dir', help='Installation directory for the imputation reference panels. Default: <currrent working dir>/resources/imputationReference')
	parser.add_argument('--list', help='List of all available reference panels either already downloaded, or available for downloading', action='store_true')
	parser.add_argument('--dl_tools', help='download all necessary imputation tools', action='store_true')
	parser.add_argument('--dl_reference', help='download and install an imputation reference panel')
	parser.add_argument('--study', help='Absolute path of the directory off the study panel')
	parser.add_argument('--output', help='Absolute path of the output (results) directory')
	parser.add_argument('--additional_shapeit_parameters', help='Extra command line arguments to pass to SHAPEIT tool', default=' ')
	parser.add_argument('--additional_impute2_parameters', help='Extra command line arguments to pass to impute2 tool', default=' ')
	parser.add_argument('--position_batch_size', help='Size of the chromosomal position of each imputation batch', default=5000000)
	parser.add_argument('--sample_batch_size', help='Minimum number of samples in imputation batches', default=500)
	parser.add_argument('--reference', help='name of the imputation reference panel')
	parser.add_argument('--action', help='Action to do: liftover, phase, impute', choices=['liftover', 'phase', 'impute'])
	parser.add_argument('--backend', help='Execution environment. Default: local', choices=['pbs',  'grid', 'local'], default='local')
	
	args = parser.parse_args()

	imp = Imputation(dl_tools=args.dl_tools, reference_dir=args.reference_dir)

	if args.dl_tools:
		imp.install_imputation_tools()

	elif args.list:
		imp.list_reference_panels()

	elif args.dl_reference:
		imp.install_reference_panel(args.dl_reference)

	if args.action:
		if not args.study:
			raise Exception('You need to define a directory where the study panel is, in order to perform this action (parameter --study)')

		if not args.output:
			raise Exception('You need to define a directory where the output results will be stored (parameter --output')

		if args.action == 'liftover':
			imp.perform_liftover(args.study, args.output, backend=args.backend)

		elif args.action == 'phase':
			imp.perform_phase(args.study, args.output, additional_shapeit_parameters=args.additional_shapeit_parameters, backend=args.backend)

		elif args.action == 'impute':
			if not args.reference:
				raise Exception('You need to define a reference panel. Use the --reference parameter. For a list for all available reference panels, use --list')

			imp.perform_phase(args.study, args.output, args.reference, 
				additional_impute2_parameters=args.additional_impute2_parameters, 
				sample_batch_size=args.sample_batch_size,
				position_batch_size=args.position_batch_size,
				backend=args.backend)


