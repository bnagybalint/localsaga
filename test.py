from pysaga import Task, CallableTask
from pysaga import LocalSaga, SagaFailed, CompensationFailed

def update_db(ctx):
	new_id = '02823148dfe20'
	print('Updateing DB: new ID is {}'.format(new_id))
	ctx.id = new_id
def compensate_db(ctx):
	print('Removing from DB: {}'.format(ctx.id))

def dummy(ctx):
	print('Dummy')

class WriteFileTask(Task):
	def execute(self, ctx):
		filename = 'C:/foo/bar.png'
		print('Writing file {}'.format(filename))
		ctx.filename = filename

	def compensate(self, ctx):
		print('Deleting file {}'.format(ctx.filename))

def failure(ctx):
	raise RuntimeError('Division by zero, the Universe flipped inside out.')

if __name__ == '__main__':

	try:
		saga = LocalSaga()

		# saga step with task object
		saga.execute(WriteFileTask())

		# saga step using functions
		saga.execute(CallableTask(update_db, compensate_db), name='Update DB')

		# saga step with no compensate
		saga.execute(CallableTask(dummy))

		# saga step to fail at compensation
		#saga.execute(CallableTask(dummy, failure))
		# saga step to fail
		#saga.execute(CallableTask(failure, dummy))
		
		print('Saga succeeded!')

		saga.compensate()

		print('Saga compensated anyway.')
		
	except SagaFailed as e:
		print('Saga failed!')
		print('  reason: {}'.format(str(e)))
	except CompensationFailed as e:
		print('Saga compensation failed!')
		print('  reason: {}'.format(str(e)))