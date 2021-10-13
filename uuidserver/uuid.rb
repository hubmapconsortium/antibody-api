require 'json'
require 'securerandom'
require 'sinatra'

set :bind, '0.0.0.0'
set :port , 80

before do
  content_type :json
end

post '/hmuuid' do
  [{ 
    uuid: SecureRandom.uuid,
    hubmap_base_id: 1,
    hubmap_id: 2
  }].to_json
end

post '/file-upload' do
  { temp_file_id: 'temp_file_id' }.to_json
end

post '/file-commit' do
  {
    file_uuid: SecureRandom.uuid,
    filename: "example-avr-report.pdf"
  }.to_json
end
