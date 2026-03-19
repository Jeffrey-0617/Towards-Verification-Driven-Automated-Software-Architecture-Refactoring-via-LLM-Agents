You are provided with misconfiguration rules and illegal attachment statements. Please follow fix the illegal attachment statements in the given Wright# scripts.


One port can only be attached to one input role.



The following ports are illegally attached to multiple input roles, violating the constraint that each port can only be attached to one input role:
Issue 1: the port MediaEncoder.encode_capture is attached to multiple input roles: ['aec_to_encoder.handler()', 'screencapturer_to_encoder.handler()']
The illegal attachment statement is:
attach MediaEncoder.encode_capture() = aec_to_encoder.handler() <*> screencapturer_to_encoder.handler() <*> encoder_to_h264.forwarder(306) <*> encoder_to_crypto_stream.forwarder(307) <*> encoder_to_recording.forwarder(308);

Constraint: Each port on the left-hand side can only be attached to one input role. To handle multiple input roles, you need to create additional ports.
Request: Please provide the refined attachment statements that resolve these violations by creating new ports as needed.

*** ONLY Output the final fixed Wright# scripts (only new attachments) ***
