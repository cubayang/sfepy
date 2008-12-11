from sfepy.base.base import *
from sfepy.applications import SimpleApp
from coefs import MiniAppBase

class HomogenizationEngine( SimpleApp ):

    def process_options( options ):
        get = options.get_default_attr

        post_process_hook = get( 'post_process_hook', None )
        file_per_var = get( 'file_per_var', False )

        coefs = get( 'coefs', None, 'missing "coefs" in options!' )
        requirements = get( 'requirements', None,
                            'missing "requirements" in options!' )

        return Struct( **locals() )
    process_options = staticmethod( process_options )

    def __init__( self, conf, options, output_prefix, volume = 1.0, **kwargs ):
        SimpleApp.__init__( self, conf, options, output_prefix,
                            init_variables = False, init_equations = False )

        self.volume = volume
    
        self.app_options = self.process_options( self.conf.options )

        post_process_hook = self.app_options.post_process_hook
        if post_process_hook is not None:
            post_process_hook = getattr( conf.funmod, post_process_hook )

        self.post_process_hook = post_process_hook

    def call( self ):
        """Application options have to be re-processed here to work with
        paramtric hooks."""
        opts = self.app_options = self.process_options( self.conf.options )

        problem = self.problem

        dependencies = {}

        coefs = Struct()

        coef_info = getattr( self.conf, opts.coefs )
        req_info = getattr( self.conf, opts.requirements )

        for coef_name, cargs in coef_info.iteritems():
            output( 'computing %s...' % coef_name )
            requires = cargs.get( 'requires', [] )
            
            for req in requires:
                if req in dependencies and (dependencies[req] is not None):
                    continue

                output( 'computing dependency %s...' % req )

                kwargs = req_info[req]

                save_name = kwargs.get( 'save_name', '' )
                name = os.path.join( problem.output_dir, save_name )

                mini_app = MiniAppBase.any_from_conf( req, problem, kwargs )
                save_hook = mini_app.make_save_hook( name,
                                                     problem.output_format,
                                                     self.post_process_hook )

#                print mini_app
                dep = mini_app( data = dependencies, save_hook = save_hook )

                dependencies[req] = dep
                output( '...done' )

#                print dep
#                pause()

            mini_app = MiniAppBase.any_from_conf( coef_name, problem, cargs )
            val = mini_app( self.volume, data = dependencies )
            print val
            setattr( coefs, cargs['mat_name'], val )
#            pause()
            output( '...done' )

        return coefs
