#! /bin/bash

wrk() {
        for ((i=$2; i<=$1; i+=$2)) ;
                {
                        echo "Rate:" $(($i))
                        /local/wrk2/wrk -t8 -c128 -L "-R"$i -d30s $3 > $4/"t8-c128-R"$i".log"
                        sleep 20
                }
        }

wrk $1 $2 $3 $4

for f in $4/*; do
        throughput=`cat $f | grep Requests/sec | awk '{print $2}'`
        latency=`cat $f | grep -m 1 Latency | awk '{print $2}'`
        echo "$f;$throughput;$latency" >> $4/result
done
