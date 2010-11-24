# -------------------------------------------------------------------------- #
# Copyright 2010, University of Chicago                                      #
#                                                                            #
# Licensed under the Apache License, Version 2.0 (the "License"); you may    #
# not use this file except in compliance with the License. You may obtain    #
# a copy of the License at                                                   #
#                                                                            #
# http://www.apache.org/licenses/LICENSE-2.0                                 #
#                                                                            #
# Unless required by applicable law or agreed to in writing, software        #
# distributed under the License is distributed on an "AS IS" BASIS,          #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.   #
# See the License for the specific language governing permissions and        #
# limitations under the License.                                             #
# -------------------------------------------------------------------------- #

module FileHelper
	def add_line(file, line)
	   f = File.open(file, "a+")
	   if f.grep(Regexp.new(Regexp.quote(line))).length == 0:
	     f.puts("#{line}")
	     f.close()
	     return true
	   end
	   f.close()
	   return false
	end
end


module MiscHelper
	def ip2orgletter(ip)
		(?a + ip.split(".")[2].to_i - 100).chr
	end
end
