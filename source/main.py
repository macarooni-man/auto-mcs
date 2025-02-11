from wrapper import launch_automcs
import sys
import os
import gc


# Android launcher
if __name__ == '__main__':
    os.environ['SDL_VIDEO_SCALE_MODE'] = 'stretch'

    from jnius import autoclass, PythonJavaClass, java_method
    import constants

    # Get the Android activity
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity


    # Define a PythonJavaClass implementing java/lang/Runnable without overriding __init__
    class Runnable(PythonJavaClass):
        __javainterfaces__ = ['java/lang/Runnable']
        __javacontext__ = 'app'

        @java_method('()V')
        def run(self):
            # Check if a function has been assigned; if so, call it.
            if hasattr(self, 'func'):
                self.func()


    def update_window_configuration():
        # Get the DisplayMetrics to determine the phone's resolution.
        DisplayMetrics = autoclass('android.util.DisplayMetrics')
        dm = DisplayMetrics()
        activity.getWindowManager().getDefaultDisplay().getMetrics(dm)
        phone_width = int(dm.widthPixels)
        phone_height = int(dm.heightPixels)

        # Set the scale factor dynamically, 2.0 will half the resolution
        min_height = 720
        constants.scale_factor = phone_height / min_height

        # Calculate the virtual resolution.
        virtual_width = round(phone_width / constants.scale_factor)
        virtual_height = round(phone_height / constants.scale_factor)
        constants.window_size = (virtual_width, virtual_height)

        SDLActivity = autoclass('org.libsdl.app.SDLActivity')
        mSurface = SDLActivity.mSurface  # This should be an SDLSurface (SurfaceView)
        mHolder = mSurface.getHolder()
        mHolder.setFixedSize(virtual_width, virtual_height)

        layoutParams = mSurface.getLayoutParams()
        LayoutParams = autoclass('android.view.ViewGroup$LayoutParams')

        layoutParams.width = LayoutParams.MATCH_PARENT
        layoutParams.height = LayoutParams.MATCH_PARENT
        mSurface.setLayoutParams(layoutParams)

        # Get default system language
        try:
            system_locale = autoclass('java.util.Locale').getDefault().getLanguage()

            for v in constants.available_locales.values():
                if system_locale.startswith(v['code']):
                    if not constants.app_config.locale:
                        constants.app_config.locale = v['code']
                    break
        except Exception as e:
            print(f'Failed to determine locale: {e}')

        if not constants.app_config.locale:
            constants.app_config.locale = 'en'


    # Create an instance of Runnable, then assign the function attribute.
    runnable = Runnable()
    runnable.func = update_window_configuration
    activity.runOnUiThread(runnable)



    # Modify garbage collector
    gc.collect(2)
    gc.freeze()

    constants.app_compiled = True
    constants.launch_path = sys.executable
    try:
        constants.username = constants.run_proc('whoami', True).split('\\')[-1].strip()
    except:
        pass
    try:
        constants.hostname = constants.run_proc('hostname', True).strip()
    except:
        pass

    # os.environ["KIVY_NO_CONSOLELOG"] = "1"
    constants.debug = True

    # Start the app
    launch_automcs()
