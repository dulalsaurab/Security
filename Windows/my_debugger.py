from ctypes import *
from my_debugger_defines import *
kernel32 = windll.kernel32
class debugger():
	def __init__(self):
		self.h_process = None
		self.h_thread = None
		self.pid = None
		self.debugger_active = False
		self.context = None
		
	def load(self, path_to_exe):
		# dwCreation flag determines how to create the process 
		# set creation_flags = CREATE_NEW_CONSOLE if you want 
		# to see the calculator GUI
		creation_flags = DEBUG_PROCESS
		# instantiate the structs
		startupinfo = STARTUPINFO()
		process_information = PROCESS_INFORMATION()

		# The following two options allow the started process 
		# to be shown as a separate window. This also illustrates 
		# how different settings in the STARTUPINFO struct can affect 
		# the debuggee.
		startupinfo.dwFlags = 0x1
		startupinfo.wShowWindow = 0x0
		# We then initialize the cb variable in the STARTUPINFO struct
		# which is just the size of the struct itself
		startupinfo.cb = sizeof(startupinfo)

		if kernel32.CreateProcessA(path_to_exe,
									None,
									None,
									None,
									None,
									creation_flags,
									None,
									None,
									byref(startupinfo),
									byref(process_information)):
		    print "[*] We have successfully launched the process!"	
		    print "[*] PID: %d" % process_information.dwProcessId

		    # Obtain a valid handle to the newly created process
		    # and store it for future access process id = process_information.dwProcessId

		    self.h_process = self.open_process(self, process_information.dwProcessId)
		    self.pid = process_information.dwProcessId
		    self.debugger_active = True

		else:
		    print "[*] Error: 0x%08x. " % kernel32.GetLastError()
		    
	def open_process(self, pid):
		# Obtain process handle with given process id i.e. pid
		h_process = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
		return h_process
	def open_thread(self, thread_id):
		# Obtain thread handle with given thread id i.e. tid
		h_thread = kernel32.OpenThread(THREAD_ALL_ACCESS, None, thread_id)
		if h_thread is not None:
			return h_thread
		else:
			print "[*] Could not obtain a valid thread handle."
			return False
	def enumerate_threads(self):
		thread_entry = THREADENTRY32()
		thread_list = []
		snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, self.pid)
		if snapshot is not None:
			# You have to set the size of the struct
			# or the call will fail
			thread_entry.dwSize = sizeof(thread_entry)
			success = kernel32.Thread32First(snapshot, byref(thread_entry))
			while success:
				if thread_entry.th32OwnerProcessID == self.pid:
					thread_list.append(thread_entry.th32ThreadID)
				success = kernel32.Thread32Next(snapshot, byref(thread_entry))	
			kernel32.CloseHandle(snapshot)	
			return thread_list
		else:
			return False
	
	def get_thread_context(self, thread_id = None, h_thread = None):
		context = CONTEXT()
		context.ContextFlags = CONTEXT_FULL | CONTEXT_DEBUG_REGISTERS
		# Obtain a handle to the thread
		if h_thread is None:
			self.h_thread = self.open_thread(thread_id)

		if kernel32.GetThreadContext(self.h_thread, byref(context)):
			return context
		else:
			return False
		
	def attach(self, pid):
		# attach process in debugger with given process id i.e pid
		self.h_process = self.open_process(pid);

		# We attempt to attach to the process 
		# if this fails we exit the call
		if kernel32.DebugActiveProcess(pid):
			self.debugger_active = True
			self.pid = int(pid)
			#self.run()
		else:
			print "[*] Unable to attach to the process."

	def run(self):
		# Now we have to poll the debugee for 
		# debugging events
		while self.debugger_active == True:
			self.get_debug_event()

	def get_debug_event(self):
		debug_event = DEBUG_EVENT() # from my_debugger_defines
		continue_status = DBG_CONTINUE # 
		if kernel32.WaitForDebugEvent(byref(debug_event), 100):
			# We aren't going to build any event handlers just yet.
			# Let's just resume the process for now.
			# raw_input("Press a key to continus....")
			# self.debugger_active = False
			self.h_thread = self.open_thread(debug_event.dwThreadId)
			self.context = self.get_thread_context(h_thread=self.h_thread)
			self.debug_event = debug_event

			#print "Event Code: %d Thread ID: %d" % (debug_event.dwDebugEventCode, debug_event.dwThreadId)
			#if debug_event.dwDebugEventCode == EXCEPTION_DEBUG_EVENT:
				#self.exception = debug_event.u.Exception.ExceptionRecord.ExceptionCode
				

			# For more http://msdn.microsoft.com/en-us/library/windows/desktop/ms679285%28v=vs.85%29.aspx
			kernel32.ContinueDebugEvent(debug_event.dwProcessId, debug_event.dwThreadId, continue_status)


	def detach(self):
		if kernel32.DebugActiveProcessStop(self.pid):
			print "[*] Finished debugging. Exiting..."
			return True
		else:
			print "There was an error"
			return False
			
			



			
			


