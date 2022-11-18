import csv
import simpy
import numpy as np
import datetime
import matplotlib.pyplot as plt


def parse_csv(file):
    # parses csv into to lists
    # convert service times to seconds 
    # convert invocations into invocations/second
    
    with open(file, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        lines = 0
        lam = 0
        sum_lam = 0
        avg_service_times = []
        avg_arrival_rates = []
        weights = []
        for row in csv_reader:
            avg_service_times.append(int(row["AvgServiceTimeMillisec"])/1000)
            lam = int(row["Invocations30Days"])/(30*24*60*60)
            avg_arrival_rates.append(lam)
            sum_lam += lam
            lines += 1

        # compiles a list of weights to be used in a discrete distribution sampler
        for i in range(len(avg_service_times)):
            weights.append(avg_arrival_rates[i]/sum_lam)


    return avg_service_times, weights, sum_lam


class g:
    no_runs = 1 # used to repeat with different M
    no_trials = 5 # repeats each model this many times
    sim_duration = 60*60*24 # runs sim for this many simulated seconds
    f = 10861 # no. functions
    cold_start = 0.5 #c old start rate
    avg_service_times, weights, sum_lam = parse_csv('trace-final.csv')
    

class Request:
    def __init__(self, f_id):
        self.id = f_id
    

class Faas_Model:

    def __init__(self, trial_no, m, file_name):
        self.env = simpy.Environment()

        self.trial_no = trial_no
        self.m = m
        self.results_file = file_name

        # tracks status of each f 0: not in m, 1: idle, 2: executing
        self.status = np.ones(self.m).tolist() + np.zeros(g.f-self.m).tolist()

        # initializes memory with the first m functions all idle
        self.idle_queue = np.arange(self.m).tolist()


        # measures
        self.request_counter = 0
        self.cold_start_counter = 0
        self.lost_request_counter = 0
        self.memory_full_loss = 0
        self.already_running_loss = 0
        self.completions = 0

        # lists for graphs
        self.obs_time = []
        self.obs_cold_ratio = []
        self.obs_loss_rate = []

    def generate_requests(self):
        # generates requests using aggregate poisson process
        # sample a discrete distribution to assign the request a function
        
        while True:

            yield self.env.timeout(generate_time_to_request())

            self.request_counter += 1

            r_id = int(np.random.choice(a=g.f, p=g.weights)) # split poisson to stream f
            r = Request(r_id)

            self.env.process(self.service_request(r))

    def service_request(self, request):

        # check if f is running and reject request
        if self.status[request.id] == 2:
            self.already_running_loss += 1
            self.lost_request_counter += 1

        # check if f is idle and start executing
        elif self.status[request.id] == 1:
          
            self.status[request.id] = 2
            self.env.process(self.complete_request(request))

        # if f is not in memory check if everything in memory is executing
        else:
            self.mem_in_use = self.status.count(2)

            if self.mem_in_use >= self.m:
                # m is full reject request
                self.memory_full_loss += 1
                self.lost_request_counter += 1
                
            
            else:
                # Check top of the idle queue for which function to remove   
                evict = self.idle_queue[0]
                self.status[evict] = 0
                self.idle_queue = remove_values_from_list(self.idle_queue, evict)

                self.status[request.id] = 2

                self.cold_start_counter += 1

                # sample cold start time
                yield self.env.timeout(generate_time_to_start())
            
                self.env.process(self.complete_request(request))

                
    def complete_request(self, request):
        # remove f from idle queue
        self.idle_queue = remove_values_from_list(self.idle_queue, request.id)

        # sample service time
        yield self.env.timeout(generate_time_to_service(request.id))

        self.completions += 1

        # return to idling, add f to the end of the idle queue
        self.status[request.id] = 1
        self.idle_queue.append(request.id)

    def observe(self):
        # records measure every second
        while True:
            try:
                
                self.obs_cold_ratio.append(self.cold_start_counter/self.request_counter)
                self.obs_time.append(self.env.now)
                self.obs_loss_rate.append(self.lost_request_counter/self.obs_time[-1])
            except:
                pass
            yield self.env.timeout(1)



    def run(self):

        # start sim
        self.env.process(self.generate_requests())
        self.env.process(self.observe())
        self.env.run(until=g.sim_duration)

        # Output to terminal
        print(f'\nTrial {self.trial_no+1} of {g.no_trials}')
        print(f'Simulated for {str(datetime.timedelta(seconds=g.sim_duration))}')
        print(f'M Capacity: {self.m}')

        print(f'\nRequests made: {self.request_counter}')
        print(f'Requests lost: {self.lost_request_counter}')
        print(f'Memory full lost: {self.memory_full_loss}')
        print(f'Already Running lost: {self.already_running_loss}')
        print(f'Completions: {self.completions}')
        print(f'Cold starts: {self.cold_start_counter}')

        print(f'\nCold start ratio = {self.obs_cold_ratio[-1]}')
        print(f'Loss rate = {self.obs_loss_rate[-1]}\n')

        # Output to graphs
        ax.plot(model.obs_time, model.obs_cold_ratio, label=f'{self.m}')
        ax2.plot(model.obs_time, model.obs_loss_rate, label=f'{self.m}')

        # Output to csv
        with open(self.results_file, "a") as f:
            writer = csv.writer(f, delimiter=',')
            results_to_write = [self.trial_no,
                                self.obs_cold_ratio[-1],
                                self.obs_loss_rate[-1]]
            writer.writerow(results_to_write)


def generate_time_to_request():
    # aggregated poisson
    return np.random.exponential(scale=(1.0/g.sum_lam))

def generate_time_to_service(id):
    # exponential service time sampler
    return np.random.exponential(scale=(g.avg_service_times[id]))

def generate_time_to_start():
    # exponential cold start time sampler
    return np.random.exponential(scale=1.0/g.cold_start)

def remove_values_from_list(l, val):
    # removes all values = val from list l
    c = l.count(val)
    for i in range(c):
        l.remove(val)
 
    return l


# initialize graphs
fig = plt.figure(figsize=(12, 6))

ax = fig.add_subplot(121)
ax2 = fig.add_subplot(122)

# each loop here modifies the size of m
for run in range(g.no_runs):
    m = 40 + run * 5

    #creates a cdv file for each size of m simulated and writes coloumn headers
    file_name = f'sim_out/trial_results_{m}.csv'

    with open(file_name, "w") as f:
        writer = csv.writer(f, delimiter=',')
        coloumn_headers = ["run", "cold_start_ratio", "loss_rate"]
        writer.writerow(coloumn_headers)
    
    #repeats this capacity
    for trial in range(g.no_trials):
        model = Faas_Model(trial, m, file_name)
        model.run()

#finializes and shows graphs
ax.set_title('Cold Start Ratio')
ax2.set_title('Loss Rate')

ax.set_ylim([0, 0.3])
ax.set_xlim(left=0)

ax2.set_ylim([0, 100])
ax2.set_xlim(left=0)

plt.show()
    
