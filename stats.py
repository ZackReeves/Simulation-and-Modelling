import csv
import numpy as np
import matplotlib.pyplot as plt

def parse_csv(file):
    # grabs data from sim output
    
    with open(file, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)

        n = 0
        csr = []
        lr = []

        for row in csv_reader:
            csr.append(float(row["cold_start_ratio"]))
            lr.append(float(row["loss_rate"]))
            n += 1

    return n, csr, lr

ms = []
csr_points = []
lr_points = []
csr_ci = []
lower_csr_ci = []
higher_csr_ci = []

lr_ci = []
lower_lr_ci = []
higher_lr_ci = []

#create CSVs for storing point estimtes and confidence intervals for each vlue of m

with open('data/cold_start_data.csv', "w", newline='') as f:
    writer = csv.writer(f, delimiter=',')
    coloumn_headers = ["M", "Point Estimate", "90% Confidence Interval"]
    writer.writerow(coloumn_headers)

with open('data/loss_rate_data.csv', "w", newline='') as f:
    writer = csv.writer(f, delimiter=',')
    coloumn_headers = ["M", "Point Estimate", "90% Confidence Interval"]
    writer.writerow(coloumn_headers)

#read each output
for i in range(49):
	m = 40 + i*5
	ms.append(m)
	
	file_name = f'sim_out/trial_results_{m}.csv'
	
	n, csr, lr = parse_csv(file_name)

	csr_point_est = round(np.mean(csr), 4)
	csr_points.append(csr_point_est)

	lr_point_est = round(np.mean(lr), 4)
	lr_points.append(lr_point_est)

	#calculates point estimate and confidence interval for c_ratio
	csr_confidence_interval = round((1.833*np.std(csr))/np.sqrt(n), 4)
	csr_ci.append(csr_point_est)
	lower_csr_ci.append(csr_point_est-csr_confidence_interval)
	higher_csr_ci.append(csr_point_est+csr_confidence_interval)

    #calculates point estimate and confidence interval for l_rate
	lr_confidence_interval = round((1.833*np.std(lr))/np.sqrt(n), 4)
	lr_ci.append(lr_point_est)
	lower_lr_ci.append(lr_point_est-lr_confidence_interval)
	higher_lr_ci.append(lr_point_est+lr_confidence_interval)

	print(f'M Capacity: {m}')
	print(f'Samples: {n}\n')

	print(f'Cold Start Ratio:')
	print(f'Point Estimate: {csr_point_est:.4f}')
	ci = f'({csr_point_est-csr_confidence_interval:.4f}, {csr_point_est+csr_confidence_interval:.4f})'
	print(f'Confidence Interval: {ci}\n')

	with open('data/cold_start_data.csv', "a", newline='') as f:
		writer = csv.writer(f, delimiter=',')
		results_to_write = [m, f'{csr_point_est:.4f}', ci]
		writer.writerow(results_to_write)

	print(f'Loss Rate:')
	print(f'Point Estimate: {lr_point_est:.4f}')
	ci = f'({lr_point_est-lr_confidence_interval:.4f}, {lr_point_est+lr_confidence_interval:.4f})'
	print(f'Confidence Interval: {(lr_point_est-lr_confidence_interval):.4f}, {(lr_point_est+lr_confidence_interval):.4f}\n')

	with open('data/loss_rate_data.csv', "a", newline='') as f:
		writer = csv.writer(f, delimiter=',')
		results_to_write = [m, f'{lr_point_est:.4f}', ci]
		writer.writerow(results_to_write)

fig = plt.figure(figsize=(16, 8))

ax = fig.add_subplot(121)
ax2 = fig.add_subplot(122)

ax.set_title('Cold Start Ratio')
ax2.set_title('Loss Rate')

ax.plot(ms, csr_points)
ax.plot(ms, lower_csr_ci, color='red')
ax.plot(ms, higher_csr_ci, color='red')
ax.axhline(y=0.05, color='green')

ax2.plot(ms, lr_points)
ax2.plot(ms, lower_lr_ci, color='red')
ax2.plot(ms, higher_lr_ci, color='red')

ax.set_ylim([0, 0.17])
ax.set_xlim(left=0)

ax2.set_ylim([40, 100])
ax2.set_xlim(left=0)

plt.show()
    